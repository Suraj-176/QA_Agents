import os
import json
import zipfile
import re
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.llm_adapter import LLMAdapter
from app.routes.audit_logs import log_audit

class AutomationAgentService:
    def __init__(self):
        self.static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "static"
        )
        os.makedirs(os.path.join(self.static_dir, "bootstraps"), exist_ok=True)
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _extract_blocks(self, raw_text: str) -> list:
        """Parses raw text and extracts all === START_FILE ... === END_FILE === blocks."""
        blocks = re.findall(r"===\s*START_FILE:\s*([^\s]+?)\s*===([\s\S]+?)===\s*END_FILE\s*===", raw_text)
        files_list = []
        if blocks:
            for path_str, content_str in blocks:
                files_list.append({
                    "path": path_str.strip(),
                    "content": content_str.strip()
                })
        return files_list

    async def bootstrap_framework(
        self, 
        tool: str, 
        language: str, 
        pattern: str,
        output_folder: str, 
        provider: str,
        model: str,
        api_key: str,
        db: Session
    ) -> dict:
        """
        The Ultimate 3-Step Sequential Generation Pipeline with Summary-Path Scoping!
        Breaks massive framework generations into 3 targeted LLM calls to prevent laziness,
        completely eliminating file duplications or path bleeding.
        """
        # Determine target output folder (use scratch folder if none specified)
        is_scratch_mode = False
        if not output_folder or not output_folder.strip():
            is_scratch_mode = True
            output_folder = os.path.join(self.static_dir, "bootstraps", f"scratch_{os.urandom(4).hex()}")
        else:
            output_folder = os.path.normpath(output_folder.strip())

        written_paths = []
        os.makedirs(output_folder, exist_ok=True)
        
        # Helper to determine correct language extension
        lang_ext = "ts"
        lang_clean = language.lower().strip()
        if lang_clean == "python":
            lang_ext = "py"
        elif lang_clean == "java":
            lang_ext = "java"
        elif lang_clean == "javascript":
            lang_ext = "js"

        # ---------------------------------------------------------
        # PHASE 1: FOUNDATIONS MEGA-PROMPT
        # ---------------------------------------------------------
        prompt_phase_1 = f"""Act as a Principal Test Automation Architect with 15+ years of experience building enterprise-grade, highly secure, and zero-flakiness testing infrastructures for global banking platforms.

Your objective is to architect and generate the core files for a new, state-of-the-art Web and API Test Automation Framework from scratch.

### 🛠️ TECH STACK:
- Engine: {tool} ({language})
- Architecture Pattern: {pattern}
- Reporting: Allure Reports
- CI/CD: GitHub Actions

### 🏗️ STRICT ARCHITECTURAL MANDATES:
1. Split-Horizon Architecture: Strict folder segregation between UI and API tests.
2. Fluent Page Object Model: All page objects must extend BasePage, return this for method chaining, and use robust stable locators.
3. Zero Raw Assertions Policy: Step definitions must NEVER contain raw expect() statements. All assertions must be delegated to specialized Validator classes.
4. Step Traceability: Every step definition and Validator method must be wrapped in allure.step() for granular reporting.

### 🛡️ ENTERPRISE CORE ENGINES (Must address standard loopholes):
- BasePage (Anti-Flakiness): Must include exponential backoff for navigation, wait-for-visible wrappers, and robust click/fill abstractions.
- Secure Logger: A Singleton logger that automatically masks/redacts sensitive data (passwords, tokens, PANs, credit cards) before printing.
- APIClient: Secure REST wrapper methods.

--- ⚠️ EXTREMELY STRICT OUTPUT FORMAT MANDATE ⚠️ ---
You MUST output all generated files in the following parsable block-based format exactly. Do not use JSON strings or markdown wrappers around the entire response. Write each file's complete path and code content using these delimiters:

=== START_FILE: path/to/file.ext ===
[Raw, complete, and production-ready source code here]
=== END_FILE ===

You are STRICTLY FORBIDDEN from using placeholder comments like "// implement here" or "... rest of code". Every file must be fully written and syntactically correct in its raw, unescaped form.

### 📝 YOUR DELIVERABLES FOR PHASE 1:
Output the complete, production-ready code for the following foundational files:
1. package.json (or requirements.txt / pom.xml depending on language)
2. playwright.config.ts / config files
3. core/logger/Logger.{lang_ext}
4. core/api/APIClient.{lang_ext}
5. core/base/BasePage.{lang_ext}
6. .github/workflows/{tool.lower()}.yml
7. README.md

Use extremely clean code, elegant comments, and professional error handling.
"""
        print("Executing Phase 1: Generating Foundations...")
        res_phase_1 = await LLMAdapter.generate_text(provider, model, api_key, prompt_phase_1)
        files_1 = self._extract_blocks(res_phase_1)
        paths_1 = [f["path"] for f in files_1]
        
        # ---------------------------------------------------------
        # PHASE 2: HELPERS & SETUP
        # ---------------------------------------------------------
        prompt_phase_2 = f"""We are building an enterprise {tool} + {language} [{pattern}] automation framework.
In Phase 1, we successfully generated the foundational files: {paths_1}.

Now, execute PHASE 2: Write the complete, production-ready code for the setup, teardown, and retry helpers:
1. `helpers/global-setup.{lang_ext}` (must be located inside helpers/ folder)
2. `helpers/global-teardown.{lang_ext}` (must be located inside helpers/ folder)
3. `helpers/retry.{lang_ext}` (must be located inside helpers/ folder)
4. tsconfig.json (or compiler config pytest.ini)

--- ⚠️ EXTREMELY STRICT OUTPUT FORMAT MANDATE ⚠️ ---
Output your files strictly inside the === START_FILE: path === and === END_FILE === blocks.
DO NOT re-output, repeat, or duplicate any of the Phase 1 files. Generate ONLY the 4 new files listed above.
"""
        print("Executing Phase 2: Generating Helpers...")
        res_phase_2 = await LLMAdapter.generate_text(provider, model, api_key, prompt_phase_2)
        files_2 = self._extract_blocks(res_phase_2)
        paths_2 = [f["path"] for f in files_2]

        # ---------------------------------------------------------
        # PHASE 3: EXECUTIONS
        # ---------------------------------------------------------
        prompt_phase_3 = f"""We are building an enterprise {tool} + {language} [{pattern}] automation framework.
In previous phases, we successfully generated:
Foundations: {paths_1}
Helpers: {paths_2}

Now, execute PHASE 3 (The actual execution layer):
1. `src/features/ui/login.feature` & `src/features/api/api_login.feature` (Gherkin Scenarios)
2. `src/pages/loginPage.{lang_ext}` (LoginPage POM extending BasePage with fluent returns)
3. `src/steps/ui/loginPage.step.{lang_ext}` & `src/steps/api/apiLoginPage.step.{lang_ext}` (BDD step definitions wrapped in allure steps)
4. `helpers/validators/LoginValidator.{lang_ext}` (Validator class implementing Zero Assertions policy)

--- ⚠️ EXTREMELY STRICT OUTPUT FORMAT MANDATE ⚠️ ---
Output your files strictly inside the === START_FILE: path === and === END_FILE === blocks.
DO NOT re-output, repeat, or duplicate any of the previously generated files. Generate ONLY the 5 new files listed above.
"""
        print("Executing Phase 3: Generating Executions...")
        res_phase_3 = await LLMAdapter.generate_text(provider, model, api_key, prompt_phase_3)
        files_3 = self._extract_blocks(res_phase_3)

        # Combine all files generated across the 3 sequential phases
        all_files = files_1 + files_2 + files_3
        if not all_files:
            raise ValueError("LLM Pipeline completely failed to extract any formatted file blocks across all 3 phases.")

        # Write all files to disk (filtering out any path duplicates to ensure absolute security)
        written_paths_set = set()
        for file_data in all_files:
            rel_path = file_data.get("path")
            content = file_data.get("content", "")
            if not rel_path: continue
            
            clean_rel_path = os.path.normpath(rel_path).replace("..", "").lstrip("\\/").replace("\\", "/")
            
            # De-duplication check
            if clean_rel_path in written_paths_set:
                print(f"Skipping duplicate file write attempt for: {clean_rel_path}")
                continue
                
            full_path = os.path.join(output_folder, clean_rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            written_paths_set.add(clean_rel_path)
            written_paths.append(clean_rel_path)

        # Package into ZIP archive
        timestamp = int(os.urandom(4).hex(), 16)
        zip_filename = f"bootstrap_{tool.lower()}_{language.lower()}_{timestamp}.zip"
        zip_filepath = os.path.join(self.static_dir, "bootstraps", zip_filename)
        
        # Housekeeping: Purge older historical bootstrap ZIPs
        try:
            bootstraps_dir = os.path.join(self.static_dir, "bootstraps")
            for item in os.listdir(bootstraps_dir):
                if item.startswith("bootstrap_") and item.endswith(".zip"):
                    os.remove(os.path.join(bootstraps_dir, item))
        except Exception as e:
            print(f"Failed to run old bootstraps auto-purge: {e}")

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for rel_file_path in written_paths:
                src_full_path = os.path.join(output_folder, rel_file_path.replace("/", os.sep))
                zip_file.write(src_full_path, rel_file_path)

        relative_zip_url = f"bootstraps/{zip_filename}"

        # Clean up temporary scratch folder after successfully archiving into ZIP
        if is_scratch_mode:
            import shutil
            shutil.rmtree(output_folder, ignore_errors=True)
            display_folder_path = "Dynamic Memory (ZIP Download Only)"
        else:
            display_folder_path = output_folder

        log_audit(
            db=db,
            action="config",
            details=f"Sequential Mega-Prompt Pipeline finished! Scaffolded a brand-new {tool} + {language} [{pattern}] automation framework containing {len(written_paths)} files inside folder: {display_folder_path}"
        )

        return {
            "output_folder": display_folder_path,
            "zip_url": relative_zip_url,
            "files_count": len(written_paths),
            "files": written_paths,
            "status": "completed",
            "message": f"Successfully completed the 3-step AI Sequential Generation Pipeline! {len(written_paths)} files generated completely. Click the button above to download your complete repository ZIP archive."
        }

    async def generate_framework_file(self, folder_path: str, user_instruction: str, provider: str, model: str, api_key: str, db: Session) -> dict:
        raise NotImplementedError("Extend framework prompt will be handled separately.")
    def write_file_to_framework(self, folder_path: str, relative_path: str, code: str, db: Session) -> dict:
        raise NotImplementedError("Write file prompt will be handled separately.")