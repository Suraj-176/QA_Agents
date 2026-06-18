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

    async def generate_suite_from_requirements(
        self, 
        requirements_content: str, 
        title: str, 
        provider: str, 
        model: str, 
        api_key: str, 
        db: Session
    ) -> dict:
        """
        Parses requirements using an LLM provider and populates a TestCaseSuite and TestCases in the database.
        """
        prompt = f"""
        You are an expert QA Automation and Manual Testing Architect.
        Analyze the following functional requirements or user story:
        
        ---
        {requirements_content}
        ---
        
        Generate a comprehensive, professional suite of test cases to thoroughly verify these requirements. 
        Your output MUST be a valid JSON object matching the following structure EXACTLY:
        
        {{
            "title": "Name of the Test Suite",
            "test_cases": [
                {{
                    "test_id": "TC-001",
                    "title": "Clear concise summary of what is being tested",
                    "description": "Detailed explanation of the test objective",
                    "preconditions": "Preconditions required for the test (nullable)",
                    "steps": [
                        "Step 1: Action to perform",
                        "Step 2: Action to perform"
                    ],
                    "expected_result": "Detailed expectation of success",
                    "priority": "High" or "Medium" or "Low"
                }}
            ]
        }}
        
        Ensure:
        1. All critical edge cases, boundary conditions, happy paths, and error states are covered.
        2. Steps are actionable and logical.
        3. Priorities are accurately set based on user-impact.
        4. Return ONLY the JSON object. Do not include introductory text, side notes, or conversational postambles.
        """
        
        # Call LLM Adapter dynamically
        raw_llm_output = await LLMAdapter.generate_text(
            provider=provider,
            model=model,
            api_key=api_key,
            prompt=prompt
        )
        
        # Extract and parse JSON
        cleaned_json = self._clean_json_response(raw_llm_output)
        try:
            parsed_data = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM did not return a valid JSON payload: {str(e)}\nRaw Output: {raw_llm_output}")

        # Ensure suite title has a fallback
        suite_title = parsed_data.get("title") or title or "Generated Test Suite"
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
