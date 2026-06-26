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

    def _load_prompt_template(self, filename: str) -> str:
        """Loads prompt file from prompts directory dynamically."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "prompts", filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
        return ""

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

    def _clean_json_response(self, raw_text: str) -> str:
        """Safely extracts JSON from markdown-wrapped blockquotes if present anywhere in the text."""
        raw_text = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw_text)
        if match:
            return match.group(1).strip()
        return raw_text

    def scan_local_framework(self, folder_path: str) -> tuple:
        """
        Scans a local directory structure up to 4 levels deep (ignoring heavy, un-needed folders),
        and reads key configuration file contents to learn their coding style and conventions.
        Returns: (structure_tree_text, key_configs_text)
        """
        if not os.path.exists(folder_path):
            raise ValueError(f"Directory path does not exist on disk: {folder_path}")

        ignored_folders = {
            "node_modules", ".git", ".venv", "venv", "env", "target", "bin", 
            "build", ".idea", ".vscode", "dist", ".next", ".pytest_cache", "__pycache__"
        }
        
        ignored_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", 
            ".gz", ".xlsx", ".csv", ".class", ".jar", ".war"
        }

        structure_lines = []
        configs_data = []

        # 1. Crawl directory structure
        for root, dirs, files in os.walk(folder_path):
            # Prune ignored folders in-place to prevent recursive traversal
            dirs[:] = [d for d in dirs if d not in ignored_folders]
            
            depth = root[len(folder_path):].count(os.sep)
            if depth >= 4:
                continue # Limit depth to prevent token bloat
                
            indent = "  " * depth
            folder_name = os.path.basename(root) or folder_path
            structure_lines.append(f"{indent}📁 {folder_name}/")
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ignored_extensions:
                    continue
                structure_lines.append(f"{indent}  📄 {file}")
                
                # 2. Extract key config file contents (limit to 120 lines each to prevent token bloat!)
                is_config = file.lower() in [
                    "package.json", "playwright.config.ts", "playwright.config.js", 
                    "wdio.conf.js", "pom.xml", "requirements.txt", "conftest.py", 
                    "testng.xml", "basepage.js", "basepage.ts", "basetest.java"
                ] or file.endswith("basepage.py")
                
                if is_config:
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            content = "".join(lines[:120])
                            if len(lines) > 120:
                                content += "\n... [truncated due to token size optimization] ..."
                            configs_data.append(f"📄 File: {file} (Path: {os.path.relpath(filepath, folder_path)})\n```\n{content}\n```")
                    except Exception:
                        pass

        structure_tree = "\n".join(structure_lines)
        configs_text = "\n\n".join(configs_data) if configs_data else "(No key configuration files found)"
        return structure_tree, configs_text

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
        # PHASE 1: FOUNDATIONS MEGA-PROMPT (DYNAMICALLY LOADED!)
        # ---------------------------------------------------------
        tool_clean = tool.strip().capitalize()
        if tool_clean not in ["Playwright", "Selenium", "Cypress"]:
            tool_clean = "Playwright"  # Safe default fallback
            
        prompt_filename = f"{tool_clean}Bootstrap.txt"
        template = self._load_prompt_template(prompt_filename)
        
        prompt_phase_1 = template.replace("{language}", language).replace("{pattern}", pattern)
        
        print(f"Executing Phase 1: Generating Foundations using {prompt_filename}...")
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

        # Package into a highly professional, custom-tailored ZIP archive matching user selections!
        p_lower = pattern.lower()
        if "bdd" in p_lower or "cucumber" in p_lower:
            pattern_suffix = "bdd"
        elif "data" in p_lower:
            pattern_suffix = "datadriven"
        elif "api" in p_lower:
            pattern_suffix = "apihybrid"
        elif "keyword" in p_lower:
            pattern_suffix = "keyword"
        else:
            pattern_suffix = "framework"

        # Short 4-character hex suffix to prevent browser caching while keeping name gorgeous and clean!
        rand_id = os.urandom(2).hex()
        zip_filename = f"bootstrap_{tool.lower()}_{language.lower()}_{pattern_suffix}_{rand_id}.zip"
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

    async def generate_framework_file(
        self, 
        folder_path: str, 
        user_instruction: str, 
        provider: str, 
        model: str, 
        api_key: str, 
        db: Session
    ) -> dict:
        """
        Context-aware code file generator. Scans the local directory structures, loads
        conventions, and generates new POM files or spec scripts matching their style exactly.
        Natively supports generating multiple files simultaneously (e.g. features + steps + datasets)
        using our un-escapable Gherkin block delimiters!
        """
        # 1. Scan existing local context on disk
        structure_tree, configs_text = self.scan_local_framework(folder_path)

        # 2. Formulate file-generation prompt
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "prompts", "AutomationFileGen.txt")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                template = f.read().strip()
        except Exception:
            template = ""

        prompt = template.replace("{framework_structure}", structure_tree)\
                         .replace("{framework_configs}", configs_text)\
                         .replace("{user_instruction}", user_instruction)

        # 3. Call LLM Adapter dynamically
        raw_output = await LLMAdapter.generate_text(
            provider=provider,
            model=model,
            api_key=api_key,
            prompt=prompt
        )

        raw_output = raw_output.strip()

        # 4. Extract all files using our robust block parser!
        files_list = self._extract_blocks(raw_output)
        
        if files_list:
            # Symmetrical response wrapping
            return {
                "files_count": len(files_list),
                "files": files_list
            }
        else:
            # Fallback to standard JSON parser if the LLM returned JSON format
            cleaned_json = self._clean_json_response(raw_output)
            try:
                parsed_data = json.loads(cleaned_json)
                suggested_path = parsed_data.get("suggested_path") or "pages/MyNewPage.js"
                code = parsed_data.get("code") or "// Generated Code"
                return {
                    "files_count": 1,
                    "files": [{
                        "path": suggested_path,
                        "content": code
                    }]
                }
            except Exception as e:
                # Log full raw output to Uvicorn terminal for immediate diagnostics!
                print("\n" + "="*80)
                print("🚨 [CRITICAL EXTENDER ERROR] Failed to parse file generation response!")
                print(f"Error details: {str(e)}")
                print("-"*80)
                print(f"RAW LLM RESPONSE RECEIVED:\n{raw_output}")
                print("="*80 + "\n")
                raise ValueError(f"LLM did not return a valid block-based file generation: {str(e)}\nRaw Response:\n{raw_output}")

    def write_file_to_framework(self, folder_path: str, relative_path: str, code: str, db: Session) -> dict:
        """Saves generated code blocks directly into files on local disk."""
        clean_rel_path = os.path.normpath(relative_path).replace("..", "").lstrip("\\/")
        full_path = os.path.join(folder_path, clean_rel_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code)

        log_audit(
            db=db,
            action="config",
            details=f"Surgically added new file '{clean_rel_path}' directly to local framework folder: {folder_path}"
        )

        return {
            "full_path": full_path,
            "relative_path": clean_rel_path,
            "status": "success",
            "message": f"Successfully saved '{clean_rel_path}' into your framework!"
        }
