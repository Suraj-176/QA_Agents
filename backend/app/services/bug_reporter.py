import os
import json
import base64
import requests
from sqlalchemy.orm import Session
from app.models import BugReport
from app.services.llm_adapter import LLMAdapter

class BugReporterService:
    def __init__(self):
        # Configure static uploads folder
        self.static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "static"
        )
        os.makedirs(os.path.join(self.static_dir, "bugs"), exist_ok=True)

    async def analyze_screenshot_bug(
        self, 
        image_bytes: bytes, 
        filename: str,
        user_description: str, 
        provider: str, 
        model: str, 
        api_key: str, 
        db: Session
    ) -> dict:
        """
        Takes screenshot bytes, streams them dynamically to the LLM Vision model, 
        saves the local screenshot file, and registers a detailed BugReport in the database.
        """
        # 1. Save screenshot to static folder: static/bugs/{timestamp}_{filename}
        timestamp = int(os.urandom(4).hex(), 16) # Avoid collisions
        safe_filename = f"{timestamp}_{filename}"
        screenshot_filepath = os.path.join(self.static_dir, "bugs", safe_filename)
        
        with open(screenshot_filepath, "wb") as f:
            with open(screenshot_filepath, "wb") as f:
                f.write(image_bytes)
        
        relative_screenshot_path = f"bugs/{safe_filename}"

        # 2. Formulate visual audit prompt
        prompt = f"""
        You are an expert Lead QA Inspector and Visual Bug Assessor.
        Analyze this screenshot in combination with the following user report:
        
        ---
        User description: "{user_description if user_description else 'No additional details provided.'}"
        ---
        
        Perform a rigorous visual audit of the screenshot. Search for:
        1. Structural layout breakages (overlapping text, elements wrapping awkwardly, clipping blocks).
        2. Visual rendering errors (unloaded images, broken graphics, missing icons, incomplete frames).
        3. Textual exceptions (visible HTTP 404, 500 status codes, raw JSON dumps on screen, alert prompts, stack trace outputs).
        4. Inconsistent alignments or broken spacing.
        
        Your output MUST be a valid JSON object matching the following structure EXACTLY. Return ONLY the JSON:
        
        {{
            "title": "A short, professional bug report title (e.g. '[Auth Page] Password input overlaps forgot link')",
            "description": "Thorough visual breakdown of the discovered bug, including specific coordinates or screen sections where layout shifts are located.",
            "steps_to_reproduce": [
                "Step 1: Open the page on desktop viewport size",
                "Step 2: Locate the target container element"
            ],
            "expected_result": "Detailed outline of correct visual presentation or behaviour.",
            "severity": "Critical" or "High" or "Medium" or "Low"
        }}
        
        Do not include markdown wrappers, notes, or conversational text. Return only the raw JSON.
        """

        # 3. Call LLMAdapter dynamically with visual capability
        try:
            raw_analysis = await LLMAdapter.analyze_image(
                provider=provider,
                model=model,
                api_key=api_key,
                prompt=prompt,
                image_bytes=image_bytes
            )
        except Exception as e:
            # Clean up on API failure
            if os.path.exists(screenshot_filepath):
                os.remove(screenshot_filepath)
            raise RuntimeError(f"LLM Vision integration failed: {str(e)}")

        # Extract and parse JSON
        cleaned_json = raw_analysis.strip()
        if cleaned_json.startswith("```"):
            import re
            match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", cleaned_json)
            if match:
                cleaned_json = match.group(1).strip()

        try:
            parsed_bug = json.loads(cleaned_json)
        except json.JSONDecodeError:
            # Fallback parse if JSON is nested
            parsed_bug = {
                "title": f"Visual Bug: {user_description[:50]}...",
                "description": raw_analysis,
                "steps_to_reproduce": ["Analyze uploaded screenshot."],
                "expected_result": "Visual layouts render correctly.",
                "severity": "Medium"
            }

        # Build clean description incorporating reproducible steps
        steps_text = "\n".join([f"- {s}" for s in parsed_bug.get("steps_to_reproduce", [])])
        full_description = (
            f"h3. Visual Bug Details\n{parsed_bug.get('description', '')}\n\n"
            f"h3. Steps to Reproduce\n{steps_text}\n\n"
            f"h3. Expected Result\n{parsed_bug.get('expected_result', '')}"
        )

        # 4. Save BugReport in SQLite database
        bug_report = BugReport(
            title=parsed_bug.get("title") or f"Visual Bug on Screenshot {timestamp}",
            description=full_description,
            severity=parsed_bug.get("severity") or "Medium",
            screenshot_path=relative_screenshot_path,
            ai_analysis=raw_analysis,
            status="draft"
        )
        db.add(bug_report)
        db.commit()

        return {
            "bug_id": bug_report.id,
            "title": bug_report.title,
            "description": bug_report.description,
            "severity": bug_report.severity,
            "screenshot_path": bug_report.screenshot_path,
            "status": bug_report.status
        }

    async def export_to_jira(
        self, 
        bug_report_id: int, 
        jira_domain: str, 
        jira_email: str, 
        jira_token: str, 
        jira_project: str, 
        db: Session
    ) -> dict:
        """
        Dynamically connects to Atlassian JIRA Cloud REST API, creates an issue ticket, 
        uploads the visual bug screenshot attachment, and updates the database record.
        """
        bug = db.query(BugReport).filter(BugReport.id == bug_report_id).first()
        if not bug:
            raise ValueError(f"Bug report {bug_report_id} does not exist.")

        # Prepare payload mapping severity to standard Jira Priorities
        priority_map = {
            "Critical": "Highest",
            "High": "High",
            "Medium": "Medium",
            "Low": "Lowest"
        }
        jira_priority = priority_map.get(bug.severity, "Medium")

        # Basic Auth credentials base64 encoding
        auth_str = f"{jira_email}:{jira_token}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Issue schema matching Jira v3 REST API
        issue_payload = {
            "fields": {
                "project": {
                    "key": jira_project.upper().strip()
                },
                "summary": bug.title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": bug.description.replace("h3. ", "").replace("\n", " ")
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "name": "Bug"
                },
                "priority": {
                    "name": jira_priority
                }
            }
        }

        jira_domain_clean = jira_domain.replace(".atlassian.net", "").strip()
        create_issue_url = f"https://{jira_domain_clean}.atlassian.net/rest/api/3/issue"

        # 1. Post Issue Creation
        response = requests.post(create_issue_url, json=issue_payload, headers=headers)
        if response.status_code not in [200, 201]:
            raise RuntimeError(f"JIRA issue creation failed ({response.status_code}): {response.text}")

        res_data = response.json()
        issue_key = res_data.get("key")
        issue_id = res_data.get("id")
        issue_self_url = res_data.get("self")
        jira_web_url = f"https://{jira_domain_clean}.atlassian.net/browse/{issue_key}"

        # 2. Attach visual screenshot if present
        if bug.screenshot_path:
            full_screenshot_path = os.path.join(self.static_dir, bug.screenshot_path)
            if os.path.exists(full_screenshot_path):
                attachment_url = f"https://{jira_domain_clean}.atlassian.net/rest/api/3/issue/{issue_key}/attachments"
                
                # Attachment API requires standard X-Atlassian-Token header
                attach_headers = {
                    "Authorization": f"Basic {b64_auth}",
                    "X-Atlassian-Token": "no-check"
                }

                try:
                    with open(full_screenshot_path, "rb") as image_file:
                        files = {
                            "file": (os.path.basename(full_screenshot_path), image_file, "image/png")
                        }
                        attach_res = requests.post(attachment_url, files=files, headers=attach_headers)
                except Exception as attach_err:
                    # Non-fatal error; log attachment issue but issue is created
                    pass

        # 3. Update database record
        bug.jira_key = issue_key
        bug.jira_url = jira_web_url
        bug.status = "submitted_to_jira"
        db.commit()

        return {
            "bug_id": bug.id,
            "jira_key": bug.jira_key,
            "jira_url": bug.jira_url,
            "status": bug.status
        }
