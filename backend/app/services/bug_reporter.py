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

    def _load_bug_prompt(self) -> str:
        """Loads BugReportPrompt.txt from prompts folder dynamically."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "prompts", "BugReportPrompt.txt")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
        return """
        Generate a professional, structured bug report formatted cleanly for standard tracker tools (Jira, DevOps). 
        Analyze user report details: "{user_description}"
        Return ONLY a JSON object with title, description, steps_to_reproduce, expected_result, and severity.
        """

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
        Ingests user description and optional screenshot bytes. Streams dynamically to the LLM.
        Saves local screenshot files if provided, and registers a detailed BugReport in the database.
        """
        has_image = bool(image_bytes)
        screenshot_filepath = None
        relative_screenshot_path = None
        timestamp = int(os.urandom(4).hex(), 16)

        # 1. Optionally save screenshot to static folder
        if has_image:
            safe_filename = f"{timestamp}_{filename}"
            screenshot_filepath = os.path.join(self.static_dir, "bugs", safe_filename)
            # Ensure the destination folder dynamically exists on the file system
            os.makedirs(os.path.dirname(screenshot_filepath), exist_ok=True)
            with open(screenshot_filepath, "wb") as f:
                f.write(image_bytes)
            relative_screenshot_path = f"bugs/{safe_filename}"

        # 2. Formulate dynamic prompt
        base_prompt_template = self._load_bug_prompt()
        prompt = base_prompt_template.replace("{user_description}", user_description if user_description else 'No additional details provided.')

        # 3. Call LLMAdapter dynamically
        try:
            if has_image:
                raw_analysis = await LLMAdapter.analyze_image(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    prompt=prompt,
                    image_bytes=image_bytes
                )
            else:
                raw_analysis = await LLMAdapter.generate_text(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    prompt=prompt
                )
        except Exception as e:
            if has_image and screenshot_filepath and os.path.exists(screenshot_filepath):
                os.remove(screenshot_filepath)
            raise RuntimeError(f"LLM Bug Analyzer integration failed: {str(e)}")

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
            parsed_bug = {
                "title": f"Reported Bug: {user_description[:50]}..." if user_description else f"QA Bug {timestamp}",
                "description": raw_analysis,
                "steps_to_reproduce": ["Analyze reported details."],
                "expected_result": "System layouts and flows render correctly.",
                "severity": "Medium"
            }

        # Build clean description incorporating reproducible steps
        steps_text = "\n".join([f"- {s}" for s in parsed_bug.get("steps_to_reproduce", [])])
        header_text = "Visual Bug Details" if has_image else "Bug Details"
        full_description = (
            f"h3. {header_text}\n{parsed_bug.get('description', '')}\n\n"
            f"h3. Steps to Reproduce\n{steps_text}\n\n"
            f"h3. Expected Result\n{parsed_bug.get('expected_result', '')}"
        )

        # 4. Save BugReport in SQLite database
        bug_report = BugReport(
            title=parsed_bug.get("title") or (f"Visual Bug {timestamp}" if has_image else f"Functional Bug {timestamp}"),
            description=full_description,
            severity=parsed_bug.get("severity") or "Medium",
            screenshot_path=relative_screenshot_path,
            ai_analysis=raw_analysis,
            status="draft"
        )
        db.add(bug_report)
        db.commit()

        # Write to audit logs
        try:
            from app.routes.audit_logs import log_audit
            log_audit(db, "bug_reporter", f"Drafted visual bug report '{bug_report.title}' with severity: {bug_report.severity}")
        except Exception:
            pass

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
        bug: BugReport, 
        jira_domain: str, 
        jira_email: str, 
        jira_token: str, 
        jira_project: str, 
        db: Session
    ) -> dict:
        """Publishes the BugReport to JIRA Cloud REST APIs, uploading screenshot as direct attachment."""
        # Sanitize credentials (strip potential copy-paste whitespace)
        jira_domain = jira_domain.strip() if jira_domain else ""
        jira_email = jira_email.strip() if jira_email else ""
        jira_token = jira_token.strip() if jira_token else ""
        jira_project = jira_project.strip() if jira_project else ""

        priority_map = {"Critical": "Highest", "High": "High", "Medium": "Medium", "Low": "Lowest"}
        jira_priority = priority_map.get(bug.severity, "Medium")

        auth_str = f"{jira_email}:{jira_token}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # For Jira Cloud, we attach the file physically, and also embed a local link inside description
        formatted_description = bug.description
        if bug.screenshot_path:
            formatted_description += f"\n\n*Local Screen Reference:* http://127.0.0.1:5000/static/{bug.screenshot_path}"

        issue_payload = {
            "fields": {
                "project": {"key": jira_project.upper().strip()},
                "summary": bug.title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": formatted_description.replace("h3. ", "").replace("\n", " ")}]
                        }
                    ]
                },
                "issuetype": {"name": "Bug"},
                "priority": {"name": jira_priority}
            }
        }

        jira_domain_clean = jira_domain.replace(".atlassian.net", "").strip()
        create_issue_url = f"https://{jira_domain_clean}.atlassian.net/rest/api/3/issue"

        response = requests.post(create_issue_url, json=issue_payload, headers=headers)
        if response.status_code not in [200, 201]:
            raise RuntimeError(f"JIRA issue creation failed ({response.status_code}): {response.text}")

        res_data = response.json()
        issue_key = res_data.get("key")
        jira_web_url = f"https://{jira_domain_clean}.atlassian.net/browse/{issue_key}"

        # Attach visual screenshot if present
        if bug.screenshot_path:
            full_screenshot_path = os.path.join(self.static_dir, bug.screenshot_path)
            if os.path.exists(full_screenshot_path):
                attachment_url = f"https://{jira_domain_clean}.atlassian.net/rest/api/3/issue/{issue_key}/attachments"
                attach_headers = {"Authorization": f"Basic {b64_auth}", "X-Atlassian-Token": "no-check"}
                try:
                    with open(full_screenshot_path, "rb") as image_file:
                        files = {"file": (os.path.basename(full_screenshot_path), image_file, "image/png")}
                        requests.post(attachment_url, files=files, headers=attach_headers)
                except Exception:
                    pass

        bug.jira_key = issue_key
        bug.jira_url = jira_web_url
        bug.status = "submitted_to_jira"
        db.commit()

        return {"ticket_key": bug.jira_key, "ticket_url": bug.jira_url, "status": bug.status}

    async def export_to_azure_devops(
        self, 
        bug: BugReport, 
        organization: str, 
        project: str, 
        personal_access_token: str, 
        db: Session
    ) -> dict:
        """Publishes the BugReport to Azure DevOps Boards, embedding the local screenshot directly."""
        # Sanitize credentials (strip potential copy-paste whitespace)
        organization = organization.strip() if organization else ""
        project = project.strip() if project else ""
        personal_access_token = personal_access_token.strip() if personal_access_token else ""

        headers = {
            "Content-Type": "application/json-patch+json"
        }

        severity_map = {"Critical": "1 - Critical", "High": "2 - High", "Medium": "3 - Medium", "Low": "4 - Low"}
        devops_severity = severity_map.get(bug.severity, "3 - Medium")

        # Compile Description & Embed local screenshot image tag dynamically
        formatted_desc = bug.description.replace("\n", "<br/>")
        if bug.screenshot_path:
            local_image_url = f"http://127.0.0.1:5000/static/{bug.screenshot_path}"
            formatted_desc += f"<br/><br/><h3>Audited Screenshot</h3><br/><img src='{local_image_url}' alt='Bug Screenshot' width='600' />"

        patch_payload = [
            {"op": "add", "path": "/fields/System.Title", "value": bug.title},
            {"op": "add", "path": "/fields/System.Description", "value": formatted_desc},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Severity", "value": devops_severity}
        ]

        url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/$Bug?api-version=7.1"
        
        # Use requests native auth with personal access token (password parameter)
        response = requests.post(url, json=patch_payload, headers=headers, auth=("", personal_access_token))
        
        if response.status_code not in [200, 201]:
            raise RuntimeError(f"Azure DevOps Bug creation failed ({response.status_code}): {response.text}")

        res_data = response.json()
        work_item_id = str(res_data.get("id"))
        web_url = f"https://dev.azure.com/{organization}/{project}/_workitems/edit/{work_item_id}"

        bug.jira_key = f"ADO-{work_item_id}"
        bug.jira_url = web_url
        bug.status = "submitted_to_azure_devops"
        db.commit()

        return {"ticket_key": bug.jira_key, "ticket_url": bug.jira_url, "status": bug.status}

    async def export_to_github(
        self, 
        bug: BugReport, 
        owner: str, 
        repo: str, 
        personal_access_token: str, 
        db: Session
    ) -> dict:
        """Publishes the BugReport to GitHub Issues, embedding the local screenshot natively in markdown."""
        # Sanitize credentials (strip potential copy-paste whitespace)
        owner = owner.strip() if owner else ""
        repo = repo.strip() if repo else ""
        personal_access_token = personal_access_token.strip() if personal_access_token else ""

        headers = {
            "Authorization": f"token {personal_access_token}",
            "User-Agent": "QA-AI-Platform", # GitHub strictly requires a User-Agent header
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

        # Embed local screenshot image natively inside GitHub Markdown body
        body_content = bug.description
        if bug.screenshot_path:
            local_image_url = f"http://127.0.0.1:5000/static/{bug.screenshot_path}"
            body_content += f"\n\n### 🖼️ Audited Screenshot\n![Bug Screenshot]({local_image_url})"

        issue_payload = {
            "title": bug.title,
            "body": body_content,
            "labels": ["bug", f"severity:{bug.severity.lower()}"]
        }

        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        response = requests.post(url, json=issue_payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            raise RuntimeError(f"GitHub Issue creation failed ({response.status_code}): {response.text}")

        res_data = response.json()
        issue_number = str(res_data.get("number"))
        web_url = res_data.get("html_url")

        bug.jira_key = f"GH-#{issue_number}"
        bug.jira_url = web_url
        bug.status = "submitted_to_github"
        db.commit()

        return {"ticket_key": bug.jira_key, "ticket_url": bug.jira_url, "status": bug.status}

    async def export_to_gitlab(
        self, 
        bug: BugReport, 
        project_id: str, 
        personal_access_token: str, 
        db: Session
    ) -> dict:
        """Publishes the BugReport to GitLab Issues, embedding the local screenshot natively in markdown."""
        # Sanitize credentials (strip potential copy-paste whitespace)
        project_id = project_id.strip() if project_id else ""
        personal_access_token = personal_access_token.strip() if personal_access_token else ""

        headers = {
            "PRIVATE-TOKEN": personal_access_token,
            "Content-Type": "application/json"
        }

        body_content = bug.description
        if bug.screenshot_path:
            local_image_url = f"http://127.0.0.1:5000/static/{bug.screenshot_path}"
            body_content += f"\n\n### 🖼️ Audited Screenshot\n![Bug Screenshot]({local_image_url})"

        issue_payload = {
            "title": bug.title,
            "description": body_content,
            "labels": f"bug,severity:{bug.severity.lower()}"
        }

        import urllib.parse
        encoded_project = urllib.parse.quote_plus(project_id.strip())
        
        url = f"https://gitlab.com/api/v4/projects/{encoded_project}/issues"
        response = requests.post(url, json=issue_payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            raise RuntimeError(f"GitLab Issue creation failed ({response.status_code}): {response.text}")

        res_data = response.json()
        issue_iid = str(res_data.get("iid"))
        web_url = res_data.get("web_url")

        bug.jira_key = f"GL-#{issue_iid}"
        bug.jira_url = web_url
        bug.status = "submitted_to_gitlab"
        db.commit()

        return {"ticket_key": bug.jira_key, "ticket_url": bug.jira_url, "status": bug.status}

    async def test_connection(self, target: str, creds: dict) -> dict:
        """
        Executes a lightweight, non-destructive read request to the specified platform
        to verify that credentials, tokens, domains, and project keys are 100% correct.
        """
        target = target.lower().strip()
        
        try:
            if target == "jira":
                domain = creds.get("jira_domain")
                email = creds.get("jira_email")
                token = creds.get("jira_token")
                project = creds.get("jira_project")
                
                # Sanitize inputs (strip whitespaces)
                domain = domain.strip() if domain else ""
                email = email.strip() if email else ""
                token = token.strip() if token else ""
                project = project.strip() if project else ""

                if not (domain and email and token and project):
                    raise ValueError("All JIRA fields are required.")
                    
                auth_str = f"{email}:{token}"
                b64_auth = base64.b64encode(auth_str.encode()).decode()
                headers = {"Authorization": f"Basic {b64_auth}", "Accept": "application/json"}
                
                url = f"https://{domain.replace('.atlassian.net', '')}.atlassian.net/rest/api/3/project/{project.upper().strip()}"
                response = requests.get(url, headers=headers)
                
                if response.status_code == 401:
                    raise RuntimeError("Unauthorized (401): Please check your account email and JIRA API token.")
                elif response.status_code == 404:
                    raise RuntimeError(f"Not Found (404): Please check your JIRA domain and Project Key ({project}).")
                elif response.status_code != 200:
                    raise RuntimeError(f"Connection failed ({response.status_code}): {response.text}")
                    
                return {"status": "success", "message": f"Successfully connected to JIRA Project '{project}'!"}
                
            elif target == "azure_devops":
                org = creds.get("organization")
                proj = creds.get("project")
                pat = creds.get("personal_access_token")
                
                # Sanitize inputs (strip whitespaces)
                org = org.strip() if org else ""
                proj = proj.strip() if proj else ""
                pat = pat.strip() if pat else ""

                if not (org and proj and pat):
                    raise ValueError("All Azure DevOps fields are required.")
                
                # REFACTORED TO REQUIRE ONLY 'Work Items (Read)' SCOPES!
                # Querying Work Item Types list requires ONLY work item read permission (not project admin/view scope!)
                url = f"https://dev.azure.com/{org}/{proj}/_apis/wit/workitemtypes?api-version=7.1"
                
                # Use requests native Basic Auth transport layer (safest from header stripping/SSL filters)
                response = requests.get(url, auth=("", pat))
                
                if response.status_code in [401, 403]:
                    raise RuntimeError("Unauthorized (401/403): Please check your Personal Access Token (PAT) value and ensure it has 'Work Items (Read & Write)' scope enabled.")
                elif response.status_code == 404:
                    raise RuntimeError("Not Found (404): Please check your DevOps Organization name or Project name.")
                elif response.status_code != 200:
                    raise RuntimeError(f"Connection failed ({response.status_code}): {response.text}")
                    
                return {"status": "success", "message": f"Successfully connected to Azure DevOps Project '{proj}'!"}
                
            elif target == "github":
                owner = creds.get("owner")
                repo = creds.get("repo")
                pat = creds.get("personal_access_token")
                
                # Sanitize inputs (strip whitespaces)
                owner = owner.strip() if owner else ""
                repo = repo.strip() if repo else ""
                pat = pat.strip() if pat else ""

                if not (owner and repo and pat):
                    raise ValueError("All GitHub fields are required.")
                
                headers = {
                    "Authorization": f"Bearer {pat}", 
                    "User-Agent": "QA-AI-Platform",
                    "Accept": "application/vnd.github.v3+json"
                }
                url = f"https://api.github.com/repos/{owner}/{repo}"
                response = requests.get(url, headers=headers)
                
                if response.status_code == 401:
                    headers["Authorization"] = f"token {pat}"
                    response = requests.get(url, headers=headers)

                if response.status_code == 401:
                    raise RuntimeError("Unauthorized (401): Please check your GitHub Personal Access Token scopes or token value.")
                elif response.status_code == 404:
                    raise RuntimeError("Not Found (404): Please check your Repository Owner and Repository name.")
                elif response.status_code != 200:
                    raise RuntimeError(f"Connection failed ({response.status_code}): {response.text}")
                    
                return {"status": "success", "message": f"Successfully connected to GitHub Repository '{owner}/{repo}'!"}
                
            elif target == "gitlab":
                id = creds.get("project_id")
                pat = creds.get("personal_access_token")
                
                # Sanitize inputs (strip whitespaces)
                pid = id.strip() if id else ""
                pat = pat.strip() if pat else ""

                if not (pid and pat):
                    raise ValueError("All GitLab fields are required.")
                    
                headers = {"PRIVATE-TOKEN": pat}
                import urllib.parse
                url = f"https://gitlab.com/api/v4/projects/{urllib.parse.quote_plus(pid.strip())}"
                response = requests.get(url, headers=headers)
                
                if response.status_code == 401:
                    raise RuntimeError("Unauthorized (401): Please check your GitLab Personal Access Token.")
                elif response.status_code == 404:
                    raise RuntimeError("Not Found (404): Please check your GitLab Project ID or Project path.")
                elif response.status_code != 200:
                    raise RuntimeError(f"Connection failed ({response.status_code}): {response.text}")
                    
                return {"status": "success", "message": f"Successfully connected to GitLab Project '{pid}'!"}
                
            else:
                raise ValueError(f"Unsupported target: {target}")
        except Exception as e:
            raise e
