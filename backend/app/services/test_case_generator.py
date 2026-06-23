import os
import json
import re
from sqlalchemy.orm import Session
from app.models import RequirementSource, TestCaseSuite, TestCase
from app.services.llm_adapter import LLMAdapter

class TestCaseGeneratorService:
    def _clean_json_response(self, raw_text: str) -> str:
        """Safely extracts JSON from markdown-wrapped blockquotes if present."""
        raw_text = raw_text.strip()
        
        # Regex to locate markdown code blocks: ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw_text)
        if match:
            return match.group(1).strip()
        
        # If no markdown block, return raw text directly
        return raw_text

    def _attempt_json_repair(self, broken_json: str) -> str:
        """
        Attempts to heuristically repair truncated or cut-off JSON arrays/objects
        by auto-completing missing closing quotes, braces, and brackets on-the-fly.
        """
        broken_json = broken_json.strip()
        
        # Balance quotes if the JSON got cut off inside a string
        if broken_json.count('"') % 2 != 0:
            broken_json += '"'
            
        # Balance array and object symbols
        open_braces = broken_json.count('{')
        close_braces = broken_json.count('}')
        open_brackets = broken_json.count('[')
        close_brackets = broken_json.count(']')
        
        # If inside an object block, close it
        if open_braces > close_braces:
            broken_json += '}' * (open_braces - close_braces)
            
        # If inside an array block, close it
        if open_brackets > close_brackets:
            broken_json += ']' * (open_brackets - close_brackets)
            
        return broken_json

    def _load_prompt_by_type(self, mode: str) -> str:
        """
        Dynamically loads independent prompt text files from backend/app/prompts/ folder.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Determine target file
        mode_clean = mode.lower().strip()
        filename = "CombinedPrompt.txt" # Default fallback
        if mode_clean == "ui":
            filename = "UIPrompt.txt"
        elif mode_clean == "functional":
            filename = "FunctionalPrompt.txt"
            
        filepath = os.path.join(base_dir, "prompts", filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass

        # absolute fallback if file read fails
        return """
        Generate a comprehensive, professional suite of test cases to thoroughly verify these requirements:
        {requirements}
        Return ONLY a JSON array containing a title string and a test_cases list with test_id, title, description, preconditions, steps, expected_result, and priority.
        """

    async def generate_suite_from_requirements(
        self, 
        requirements_content: str, 
        title: str, 
        provider: str, 
        model: str, 
        api_key: str, 
        db: Session,
        mode: str = "combined"
    ) -> dict:
        """
        Loads the configured prompt from prompts folder based on mode, 
        pipes it to the LLM, and populates SQLite test suites and cases.
        Integrates dynamic, failsafe JSON healing and regex block-rescue sweepers on trailing truncations!
        """
        # Load isolated prompt and inject requirements
        base_prompt_template = self._load_prompt_by_type(mode)
        prompt = base_prompt_template.replace("{requirements}", requirements_content)
        
        # Call LLM Adapter dynamically
        raw_llm_output = await LLMAdapter.generate_text(
            provider=provider,
            model=model,
            api_key=api_key,
            prompt=prompt
        )
        
        # Extract and parse JSON
        cleaned_json = self._clean_json_response(raw_llm_output)
        parsed_data = None
        
        try:
            parsed_data = json.loads(cleaned_json)
        except json.JSONDecodeError:
            # 1. Attempt heuristic JSON repair on trailing truncations
            repaired_json = self._attempt_json_repair(cleaned_json)
            try:
                parsed_data = json.loads(repaired_json)
            except json.JSONDecodeError as e:
                # 2. Trigger regex block rescue: extract any successfully-written individual test case objects!
                print("JSON Parsing failed on primary and repaired attempts. Initiating regex rescue sweep...")
                test_cases_list = []
                
                # Regex matches valid-looking JSON objects containing a "test_id"
                matches = re.findall(r"\{\s*\"test_id\"[\s\S]+?\}", cleaned_json)
                for block in matches:
                    try:
                        block_repaired = self._attempt_json_repair(block)
                        tc_obj = json.loads(block_repaired)
                        if tc_obj.get("test_id") or tc_obj.get("title"):
                            test_cases_list.append(tc_obj)
                    except Exception:
                        pass
                
                if test_cases_list:
                    parsed_data = {
                        "title": title or f"Rescued {mode.upper()} Suite",
                        "test_cases": test_cases_list
                    }
                else:
                    raise ValueError(f"LLM did not return a valid JSON payload: {str(e)}\nRaw Output: {raw_llm_output}")

        # Ensure suite title has a fallback
        suite_title = parsed_data.get("title") or title or f"Generated {mode.upper()} Suite"
        test_cases_list = parsed_data.get("test_cases", [])

        # Write to Database
        # 1. Store Requirement Source
        req_source = RequirementSource(
            title=title or suite_title,
            content=requirements_content
        )
        db.add(req_source)
        db.flush() # Flush to populate ID immediately

        # 2. Store Test Suite
        suite = TestCaseSuite(
            requirement_id=req_source.id,
            title=suite_title
        )
        db.add(suite)
        db.flush()

        # 3. Store individual Test Cases
        saved_test_cases = []
        for index, tc_data in enumerate(test_cases_list, start=1):
            steps = tc_data.get("steps")
            if isinstance(steps, str):
                steps = [steps]
            elif not isinstance(steps, list):
                steps = [str(steps)] if steps else []

            test_case = TestCase(
                suite_id=suite.id,
                test_id=tc_data.get("test_id") or f"TC-{index:03d}",
                title=tc_data.get("title") or f"Test Case {index}",
                description=tc_data.get("description") or "No description provided.",
                preconditions=tc_data.get("preconditions"),
                steps=steps,
                expected_result=tc_data.get("expected_result") or "Succeeds.",
                priority=tc_data.get("priority") or "Medium"
            )
            db.add(test_case)
            saved_test_cases.append(test_case)
        
        db.commit()

        # Write to audit logs
        try:
            from app.routes.audit_logs import log_audit
            log_audit(db, "testcase_generator", f"Generated test case suite '{suite.title}' containing {len(saved_test_cases)} test cases.")
        except Exception:
            pass

        # Serialize result for response
        return {
            "suite_id": suite.id,
            "requirement_id": req_source.id,
            "title": suite.title,
            "test_cases": [
                {
                    "id": tc.id,
                    "test_id": tc.test_id,
                    "title": tc.title,
                    "description": tc.description,
                    "preconditions": tc.preconditions,
                    "steps": tc.steps,
                    "expected_result": tc.expected_result,
                    "priority": tc.priority
                }
                for tc in saved_test_cases
            ]
        }
