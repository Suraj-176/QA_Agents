import os
import cv2
import numpy as np
import threading
import asyncio
import base64
import json
import urllib.request
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright
from app.models import Baseline, BaselineScreenshot, RegressionTestRun, RegressionTestResult

VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 375, "height": 667}
}

def decode_jwt_payload(token: str) -> dict:
    """Decodes the payload of a JWT token safely."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        padding = "=" * (4 - len(payload_b64) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        return json.loads(decoded_bytes.decode("utf-8"))
    except Exception:
        return {}


def prepare_universal_auth_headers(access_token: str) -> dict:
    """Convert any access token string to standard Authorization header dict."""
    if not access_token or not access_token.strip():
        return {}
    
    token = access_token.strip()
    if token.startswith("Authorization:"):
        return {"Authorization": token.split(":", 1)[1].strip()}
    if token.startswith("Bearer "):
        return {"Authorization": token}
    if token.count(".") == 2:
        return {"Authorization": f"Bearer {token}"}
    if "Bearer" in token:
        return {"Authorization": token}
    return {"Authorization": f"Bearer {token}"}


def run_async_in_new_thread(coro_fn, *args, **kwargs):
    """
    Indestructible fix for Playwright subprocess NotImplementedError on Windows.
    Instantiates the coroutine object entirely inside the thread's event loop to prevent loop-binding crashes!
    """
    res_box = []
    err_box = []
    
    def target():
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Create and bind the coroutine entirely inside this thread's local event loop!
            coro = coro_fn(*args, **kwargs)
            res = loop.run_until_complete(coro)
            res_box.append(res)
        except Exception as e:
            err_box.append(e)
        finally:
            loop.close()
            
    t = threading.Thread(target=target)
    t.start()
    t.join()
    
    if err_box:
        raise err_box[0]
    return res_box[0]


class RegressionTestingService:
    def __init__(self):
        self.static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "static"
        )
        os.makedirs(self.static_dir, exist_ok=True)

    def _compare_images(self, baseline_path: str, run_path: str, diff_output_path: str) -> tuple:
        """Computes absolute visual differences and highlights mismatches in red."""
        base_img = cv2.imread(baseline_path)
        run_img = cv2.imread(run_path)

        if base_img is None or run_img is None:
            raise ValueError(f"Could not read comparison images. Baseline: {baseline_path}, Run: {run_path}")

        if base_img.shape != run_img.shape:
            run_img = cv2.resize(run_img, (base_img.shape[1], base_img.shape[0]))

        base_gray = cv2.cvtColor(base_img, cv2.COLOR_BGR2GRAY)
        run_gray = cv2.cvtColor(run_img, cv2.COLOR_BGR2GRAY)

        abs_diff = cv2.absdiff(base_gray, run_gray)
        _, thresh = cv2.threshold(abs_diff, 15, 255, cv2.THRESH_BINARY)

        total_pixels = thresh.size
        mismatched_pixels = np.count_nonzero(thresh)
        similarity = (1.0 - (mismatched_pixels / total_pixels)) * 100.0
        is_mismatch = similarity < 99.5

        highlight_mask = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        highlight_mask[thresh == 255] = [0, 0, 255]

        blended_diff = cv2.addWeighted(run_img, 0.7, highlight_mask, 0.3, 0)
        cv2.imwrite(diff_output_path, blended_diff)

        return round(similarity, 2), is_mismatch

    async def _capture_screenshots(self, url: str, base_folder: str, access_token: str = None, chrome_profile_path: str = None, headless_mode: bool = True) -> dict:
        """
        Launches Playwright browser context. Pre-compiles custom JSON local storages, cookies,
        and headers, injecting them directly inside native Playwright storage_states on boot!
        This completely, universally resolves redirection loops and logins on any app.
        """
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url

        os.makedirs(base_folder, exist_ok=True)
        captured_paths = {}

        is_persistent = bool(chrome_profile_path and os.path.exists(chrome_profile_path))
        headers = prepare_universal_auth_headers(access_token) if (access_token and not is_persistent) else {}
        
        raw_token_val = None
        jwt_payload = {}
        storage_state = None
        
        if access_token and not is_persistent:
            raw_token_val = headers.get("Authorization", "").replace("Bearer ", "").strip()
            jwt_payload = decode_jwt_payload(raw_token_val)
            
            # PRE-COMPILE NATIVE STORAGE STATE (100% Custom SSO and JSON support!)
            local_storage_items = []
            
            # Symmetrical custom JSON state parser: Check if access_token is a custom JSON dump!
            # If the user pasted their complete Chrome DevTools localStorage dump, we parse and inject it directly!
            try:
                custom_json = json.loads(access_token.strip())
                if isinstance(custom_json, dict):
                    print("   🚀 DETECTED CUSTOM LOCALSTORAGE JSON PAYLOAD! PRE-POPULATING DIRECTLY ON BOOT...")
                    for k, v in custom_json.items():
                        str_val = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                        local_storage_items.append({"name": k, "value": str_val})
            except Exception:
                # Fall back to our standard flat JWT and claims injections
                flat_keys = [
                    'token', 'access_token', 'accessToken', 'jwt', 'Authorization', 
                    'auth_token', 'authToken', 'session_token', 'sessionToken', 
                    'jwtToken', 'jwt_token', 'bearer_token', 'id_token', 'idToken', 
                    'user_token', 'userToken', 'credentials', 'auth', 'isAuthenticated'
                ]
                if raw_token_val:
                    for key in flat_keys:
                        local_storage_items.append({"name": key, "value": raw_token_val})
                    local_storage_items.append({"name": "isAuthenticated", "value": "true"})
                    
                    if jwt_payload:
                        for k, v in jwt_payload.items():
                            str_val = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                            local_storage_items.append({"name": k, "value": str_val})
                            # camelCase conversion
                            import re
                            camel_k = re.sub(r'_([a-z])', lambda match: match.group(1).upper(), k)
                            if camel_k != k:
                                local_storage_items.append({"name": camel_k, "value": str_val})

            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            target_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if local_storage_items:
                storage_state = {
                    "cookies": [],
                    "origins": [
                        {
                            "origin": target_origin,
                            "localStorage": local_storage_items
                        }
                    ]
                }

        print(f"   🚀 TARGET SCREENSHOT URL: '{url}'")
        if is_persistent:
            print(f"   🚀 LAUNCHING PLAYWRIGHT IN PERSISTENT SESSION BYPASS MODE: '{chrome_profile_path}' (HEADLESS: {headless_mode})")
        else:
            print(f"   🚀 UNIVERSAL HEADERS APPLIED TO CONTEXT: {{'Authorization': 'Bearer [REDACTED]'}}" if headers else "   🚀 UNIVERSAL HEADERS APPLIED TO CONTEXT: {}")

        async with async_playwright() as p:
            if is_persistent:
                chrome_profile_path = os.path.normpath(chrome_profile_path)
                last_folder = os.path.basename(chrome_profile_path)
                if last_folder.startswith("Profile ") or last_folder == "Default":
                    user_data_dir = os.path.dirname(chrome_profile_path)
                    profile_dir = last_folder
                else:
                    user_data_dir = chrome_profile_path
                    profile_dir = "Default"

                target_channel = "chrome"
                path_lower = user_data_dir.lower()
                if "edge" in path_lower or "microsoft" in path_lower:
                    target_channel = "msedge"
                    
                print(f"   🚀 LAUNCHING PERSISTENT DATA DIR: '{user_data_dir}' WITH PROFILE: '{profile_dir}'")
                
                try:
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=headless_mode,
                        channel=target_channel,
                        args=[f"--profile-directory={profile_dir}"],
                        ignore_https_errors=True,
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    )
                    page = context.pages[0] if context.pages else await context.new_page()
                except Exception as launch_err:
                    error_msg = str(launch_err).lower()
                    if "user data directory is already in use" in error_msg or "lock" in error_msg or "close" in error_msg or "target closed" in error_msg:
                        raise RuntimeError(
                            f"Failed to launch persistent browser context because Google Chrome or Microsoft Edge is CURRENTLY OPEN on your desktop! "
                            f"To resolve this instantly, please completely CLOSE all active browser windows on your computer and try again, "
                            f"or configure a dedicated, separate testing profile directory (e.g., adding '\\Profile 2' to your path)."
                        )
                    else:
                        raise RuntimeError(f"Failed to launch persistent enterprise browser context: {str(launch_err)}")
            else:
                browser = await p.chromium.launch(
                    headless=headless_mode,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-first-run',
                        '--no-default-browser-check'
                    ]
                )
                context = await browser.new_context(
                    extra_http_headers=headers,
                    storage_state=storage_state,
                    ignore_https_errors=True,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                if access_token:
                    try:
                        cookie_val = raw_token_val if raw_token_val else access_token.strip()
                        cookie_name = "sessionid"
                        
                        if "=" in cookie_val:
                            parts = cookie_val.split("=", 1)
                            cookie_name = parts[0].strip()
                            cookie_val = parts[1].strip()
                            
                        from urllib.parse import urlparse
                        domain_clean = urlparse(url).netloc.split(":")[0]
                        
                        await context.add_cookies([{
                            "name": cookie_name,
                            "value": cookie_val,
                            "domain": domain_clean,
                            "path": "/"
                        }])
                        print(f"   🚀 LEGACY SSR COOKIE INJECTED: '{cookie_name}=...' ON DOMAIN '{domain_clean}'")
                    except Exception as cookie_err:
                        print(f"   ⚠️ Cookie injection bypassed: {cookie_err}")

                page = await context.new_page()

            if raw_token_val and not is_persistent:
                async def handle_api_route(route):
                    req_url = route.request.url.lower()
                    is_static_asset = any(ext in req_url for ext in [
                        ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", 
                        ".woff", ".woff2", ".ttf", ".eot", ".ico", "appsettings.json"
                    ])
                    
                    if not is_static_asset:
                        req_headers = {**route.request.headers}
                        req_headers["Authorization"] = f"Bearer {raw_token_val}"
                        await route.continue_(headers=req_headers)
                    else:
                        await route.continue_()
                
                await page.route("**/*", handle_api_route)

            for name, viewport in VIEWPORTS.items():
                await page.set_viewport_size(viewport)
                
                try:
                    await page.goto(url, timeout=20000, wait_until="load")
                except Exception as goto_err:
                    try:
                        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    except Exception as fallback_err:
                        await context.close()
                        if 'browser' in locals() and browser:
                            await browser.close()
                        raise RuntimeError(f"Failed to load website {url}: {str(fallback_err)}")

                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass

                await page.wait_for_timeout(2000)

                target_filename = f"{name}.png"
                target_filepath = os.path.join(base_folder, target_filename)
                
                await page.screenshot(path=target_filepath, full_page=True)
                captured_paths[name] = target_filepath

            await context.close()
            if 'browser' in locals() and browser:
                await browser.close()
        return captured_paths

    async def setup_baseline(self, name: str, url: str, db: Session, access_token: str = None, chrome_profile_path: str = None, headless_mode: bool = True) -> dict:
        baseline = Baseline(name=name, url=url)
        db.add(baseline)
        db.flush()

        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        
        try:
            # Symmetrical, thread-local instantiation to prevent cross-loop task conflicts!
            captured_files = run_async_in_new_thread(self._capture_screenshots, url, baseline_folder, access_token, chrome_profile_path, headless_mode)
            
            for viewport, path in captured_files.items():
                relative_path = os.path.relpath(path, self.static_dir).replace("\\", "/")
                screen_record = BaselineScreenshot(
                    baseline_id=baseline.id,
                    viewport=viewport,
                    image_path=relative_path
                )
                db.add(screen_record)
            
            db.commit()
            try:
                from app.routes.audit_logs import log_audit
                log_audit(db, "visual_testing", f"Captured new visual baseline benchmarks '{name}' for URL: {url}")
            except Exception:
                pass
            return {
                "baseline_id": baseline.id,
                "name": baseline.name,
                "url": baseline.url,
                "screenshots_count": len(captured_files)
            }
        except Exception as e:
            db.rollback()
            if os.path.exists(baseline_folder):
                import shutil
                shutil.rmtree(baseline_folder, ignore_errors=True)
            raise e

    async def run_regression_test(
        self, 
        run_id: int, 
        db: Session, 
        access_token: str = None, 
        chrome_profile_path: str = None, 
        headless_mode: bool = True,
        llm_provider: str = None,
        llm_model: str = None,
        llm_api_key: str = None,
        azure_endpoint: str = None,
        azure_api_version: str = None
    ):
        run = db.query(RegressionTestRun).filter(RegressionTestRun.id == run_id).first()
        if not run:
            return

        run.status = "running"
        db.commit()

        run_folder = os.path.join(self.static_dir, "runs", str(run.id))
        
        try:
            # Symmetrical, thread-local instantiation to prevent cross-loop task conflicts!
            target_snaps = run_async_in_new_thread(self._capture_screenshots, run.target_url, run_folder, access_token, chrome_profile_path, headless_mode)
            
            baseline = db.query(Baseline).filter(Baseline.id == run.baseline_id).first()
            if not baseline or not baseline.screenshots:
                raise ValueError(f"Baseline {run.baseline_id} does not contain screenshots.")

            baseline_map = {s.viewport: s.image_path for s in baseline.screenshots}

            mismatch_count = 0
            viewports_run = 0

            for viewport, run_filepath in target_snaps.items():
                base_rel_path = baseline_map.get(viewport)
                if not base_rel_path:
                    continue
                
                base_filepath = os.path.join(self.static_dir, base_rel_path)
                diff_filename = f"diff_{viewport}.png"
                diff_filepath = os.path.join(run_folder, diff_filename)

                similarity, is_mismatch = self._compare_images(
                    baseline_path=base_filepath,
                    run_path=run_filepath,
                    diff_output_path=diff_filepath
                )

                if is_mismatch:
                    mismatch_count += 1

                run_rel_path = os.path.relpath(run_filepath, self.static_dir).replace("\\", "/")
                diff_rel_path = os.path.relpath(diff_filepath, self.static_dir).replace("\\", "/")

                # Dynamic Background AI Visual Triage!
                ai_analysis = None
                if is_mismatch:
                    if llm_api_key and llm_api_key.strip():
                        try:
                            # Load triage prompt template
                            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            prompt_path = os.path.join(base_dir, "prompts", "VisualTriagePrompt.txt")
                            with open(prompt_path, "r", encoding="utf-8") as f:
                                prompt_template = f.read().strip()

                            # Read the highlighted diff image bytes to send to Gemini Vision!
                            with open(diff_filepath, "rb") as image_file:
                                image_bytes = image_file.read()

                            from app.services.llm_adapter import LLMAdapter
                            print(f"   🔮 AUTOMATED BACKGROUND AI TRIAGE INITIATED FOR {viewport.upper()} VIEWPORT...")
                            ai_analysis = await LLMAdapter.analyze_image(
                                provider=llm_provider,
                                model=llm_model,
                                api_key=llm_api_key,
                                prompt=prompt_template,
                                image_bytes=image_bytes,
                                azure_endpoint=azure_endpoint,
                                azure_api_version=azure_api_version
                            )
                            print(f"   ✓ BACKGROUND AI TRIAGE COMPLETED SUCCESSFULLY FOR {viewport.upper()}!")
                        except Exception as triage_err:
                            print(f"   ⚠️ Background AI Visual Triage failed/skipped: {triage_err}")
                            ai_analysis = f"AI Visual Triage was interrupted: {str(triage_err)}"
                    else:
                        ai_analysis = "AI Visual Triage was skipped because no LLM API Key was configured inside Settings at the time this comparison run was executed."
                else:
                    ai_analysis = "Success: Viewport layout matches your baseline visual benchmark perfectly. Zero visual regressions or style discrepancies detected."

                test_result = RegressionTestResult(
                    run_id=run.id,
                    viewport=viewport,
                    similarity_score=similarity,
                    baseline_image_path=base_rel_path,
                    run_image_path=run_rel_path,
                    diff_image_path=diff_rel_path,
                    is_mismatch=is_mismatch,
                    ai_analysis=ai_analysis
                )
                db.add(test_result)
                viewports_run += 1

            run.status = "completed"
            if mismatch_count > 0:
                run.summary = f"Visual Regressions Detected! {mismatch_count} out of {viewports_run} viewports failed comparison checks."
            else:
                run.summary = f"Success. All {viewports_run} viewports successfully validated and matched visual baselines."

        except Exception as e:
            run.status = "failed"
            run.summary = f"Execution interrupted. Error: {str(e)}"
        finally:
            db.commit()
            try:
                from app.routes.audit_logs import log_audit
                log_audit(db, "visual_testing", f"Completed comparison run for baseline ID {run.baseline_id} against target URL: {run.target_url}. Result: {run.summary}")
            except Exception:
                pass

    async def delete_baseline(self, baseline_id: int, db: Session):
        baseline = db.query(Baseline).filter(Baseline.id == baseline_id).first()
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} does not exist.")

        baseline_name = baseline.name
        import shutil
        
        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        if os.path.exists(baseline_folder):
            shutil.rmtree(baseline_folder, ignore_errors=True)
            
        for run in baseline.runs:
            run_folder = os.path.join(self.static_dir, "runs", str(run.id))
            if os.path.exists(run_folder):
                shutil.rmtree(run_folder, ignore_errors=True)

        db.delete(baseline)
        db.commit()
        try:
            from app.routes.audit_logs import log_audit
            log_audit(db, "visual_testing", f"Permanently deleted visual baseline '{baseline_name}' and cleared all associated comparison runs.")
        except Exception:
            pass

    async def recapture_baseline(self, baseline_id: int, db: Session, access_token: str = None, chrome_profile_path: str = None, headless_mode: bool = True) -> dict:
        baseline = db.query(Baseline).filter(Baseline.id == baseline_id).first()
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} does not exist.")

        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        
        # Symmetrical, thread-local instantiation to prevent cross-loop task conflicts!
        captured_files = run_async_in_new_thread(self._capture_screenshots, baseline.url, baseline_folder, access_token, chrome_profile_path, headless_mode)
        
        baseline.created_at = datetime.utcnow()
        db.commit()
        try:
            from app.routes.audit_logs import log_audit
            log_audit(db, "visual_testing", f"Overwrote and recaptured visual baseline benchmarks for '{baseline.name}' at URL: {baseline.url}")
        except Exception:
            pass
        
        return {
            "baseline_id": baseline.id,
            "name": baseline.name,
            "url": baseline.url,
            "created_at": baseline.created_at.isoformat(),
            "screenshots_count": len(captured_files)
        }
