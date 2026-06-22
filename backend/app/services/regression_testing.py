import os
import cv2
import numpy as np
import threading
import asyncio
import base64
import json
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
    """
    Decodes the payload of a JWT token without requiring external dependencies.
    Extracts claims such as roles, username, email, and sessionid.
    """
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
    """
    Convert any access token string to standard Authorization header dict.
    Works with: JWT, Bearer tokens, API keys, and raw custom strings.
    """
    if not access_token or not access_token.strip():
        return {}
    
    token = access_token.strip()
    
    # Already formatted as complete header (Authorization: Bearer <token>)
    if token.startswith("Authorization:"):
        return {"Authorization": token.split(":", 1)[1].strip()}
    
    # Already has "Bearer " prefix
    if token.startswith("Bearer "):
        return {"Authorization": token}
    
    # JWT token (has 3 parts separated by dots)
    if token.count(".") == 2:
        return {"Authorization": f"Bearer {token}"}
    
    # Already has "Bearer" somewhere inside the string
    if "Bearer" in token:
        return {"Authorization": token}
    
    # Default: wrap as Bearer token (works 99% of the time)
    return {"Authorization": f"Bearer {token}"}


def run_async_in_new_thread(coro):
    """
    Spawns a dedicated OS Thread, overrides Uvicorn's forced Selector loop policy,
    instantiates a fresh WindowsProactorEventLoop, and runs the coroutine to completion.
    This is the ultimate, indestructible fix for Playwright subprocess NotImplementedError on Windows.
    """
    res_box = []
    err_box = []
    
    def target():
        import sys
        # Explicitly configure Proactor loop inside this isolated thread context on Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(coro)
            res_box.append(res)
        except Exception as e:
            err_box.append(e)
        finally:
            loop.close()
            
    t = threading.Thread(target=target)
    t.start()
    t.join() # Await completion of thread execution block
    
    if err_box:
        raise err_box[0]
    return res_box[0]


class RegressionTestingService:
    def __init__(self):
        # Configure local directory where files are hosted
        self.static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "static"
        )
        os.makedirs(self.static_dir, exist_ok=True)

    def _compare_images(self, baseline_path: str, run_path: str, diff_output_path: str) -> tuple:
        """
        Loads baseline and target run images, computes absolute visual differences,
        and generates a blended overlay highlighting mismatches in red.
        Returns: (similarity_score: float, is_mismatch: bool)
        """
        base_img = cv2.imread(baseline_path)
        run_img = cv2.imread(run_path)

        if base_img is None or run_img is None:
            raise ValueError(f"Could not read comparison images. Baseline: {baseline_path}, Run: {run_path}")

        # Ensure identical sizes for visual subtraction
        if base_img.shape != run_img.shape:
            run_img = cv2.resize(run_img, (base_img.shape[1], base_img.shape[0]))

        # Convert to grayscale to simplify subtraction and calculation
        base_gray = cv2.cvtColor(base_img, cv2.COLOR_BGR2GRAY)
        run_gray = cv2.cvtColor(run_img, cv2.COLOR_BGR2GRAY)

        # Calculate pixel difference
        abs_diff = cv2.absdiff(base_gray, run_gray)

        # Threshold difference image to segment shifts
        _, thresh = cv2.threshold(abs_diff, 15, 255, cv2.THRESH_BINARY)

        # Calculate percentage similarity
        total_pixels = thresh.size
        mismatched_pixels = np.count_nonzero(thresh)
        similarity = (1.0 - (mismatched_pixels / total_pixels)) * 100.0

        # High similarity limit (any score below 99.5 is classified as a layout regression)
        is_mismatch = similarity < 99.5

        # Create color highlight overlay (White pixels turned to RED)
        highlight_mask = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        highlight_mask[thresh == 255] = [0, 0, 255] # Red outline in BGR

        # Blend original target image with red mask
        blended_diff = cv2.addWeighted(run_img, 0.7, highlight_mask, 0.3, 0)
        cv2.imwrite(diff_output_path, blended_diff)

        return round(similarity, 2), is_mismatch

    async def _capture_screenshots(self, url: str, base_folder: str, access_token: str = None) -> dict:
        """
        Launches Playwright headless browser context with universal auth headers applied automatically 
        to ALL outgoing requests, decodes JWT payloads, pre-injects all user claims, access tokens, and 
        isAuthenticated=true session values into LocalStorage and SessionStorage context, and captures screenshots.
        """
        # Automatically prepend http:// if protocol is missing (e.g. www.google.com)
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url

        os.makedirs(base_folder, exist_ok=True)
        captured_paths = {}

        # 1. Prepare standard universal Authorization Header
        headers = prepare_universal_auth_headers(access_token) if access_token else {}
        
        # Extract JWT claims payload for localized state injections
        raw_token_val = None
        jwt_payload = {}
        if access_token:
            raw_token_val = headers.get("Authorization", "").replace("Bearer ", "").strip()
            jwt_payload = decode_jwt_payload(raw_token_val)

        print(f"   🚀 TARGET SCREENSHOT URL: '{url}'")
        print(f"   🚀 UNIVERSAL HEADERS APPLIED TO CONTEXT: {{'Authorization': 'Bearer [REDACTED]'}}" if headers else "   🚀 UNIVERSAL HEADERS APPLIED TO CONTEXT: {}")

        async with async_playwright() as p:
            # Launch fresh, lightweight automated browser sandbox
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check'
                ]
            )
            # Apply HTTP headers to ALL outgoing page/AJAX requests natively!
            context = await browser.new_context(
                extra_http_headers=headers,
                ignore_https_errors=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            # 🚀 NATIVE GLOBAL NETWORK ROUTE INTERCEPTOR (For ALL API backend handshakes)
            # This is the gold-standard fix for Playwright stripping Authorization headers across different ports (8012 -> 8013)!
            # Intercepts 100% of AJAX requests globally while cleanly bypassing Next.js static asset bundles!
            if raw_token_val:
                async def handle_api_route(route):
                    req_url = route.request.url.lower()
                    
                    # Define list of static file extensions to skip from header injection (prevents Next.js crashes)
                    is_static_asset = any(ext in req_url for ext in [
                        ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", 
                        ".woff", ".woff2", ".ttf", ".eot", ".ico", "appsettings.json"
                    ])
                    
                    if not is_static_asset:
                        req_headers = {**route.request.headers}
                        # Force inject the Bearer Token directly into the Authorization header!
                        req_headers["Authorization"] = f"Bearer {raw_token_val}"
                        await route.continue_(headers=req_headers)
                    else:
                        await route.continue_()
                
                # Intercept ALL requests globally on the context level!
                await page.route("**/*", handle_api_route)

            for name, viewport in VIEWPORTS.items():
                await page.set_viewport_size(viewport)
                
                # 2. JIT LocalStorage & SessionStorage Injection (Universal SPA login bypass)
                if raw_token_val:
                    try:
                        # Fast-navigate to commit state to enter the domain's security origin sandbox
                        await page.goto(url, timeout=15000, wait_until="commit")
                        
                        # Pre-inject Bearer Token, claims, AND standard session keys dynamically
                        await page.evaluate("""([token, payload]) => {
                            // Set the active session confirmation keys!
                            localStorage.setItem('isAuthenticated', 'true');
                            sessionStorage.setItem('isAuthenticated', 'true');

                            // List of standard simple key names
                            const flatKeys = [
                                'token', 'access_token', 'accessToken', 'jwt', 'Authorization', 
                                'auth_token', 'authToken', 'session_token', 'sessionToken', 
                                'jwtToken', 'jwt_token', 'bearer_token', 'id_token', 'idToken', 
                                'user_token', 'userToken', 'credentials', 'auth'
                            ];
                            
                            // Write flat keys
                            if (token) {
                                for (const key of flatKeys) {
                                    localStorage.setItem(key, token);
                                    sessionStorage.setItem(key, token);
                                }
                            }
                            
                            if (payload) {
                                // Write all individual claims from decoded JWT as flat items
                                for (const [key, val] of Object.entries(payload)) {
                                    const strVal = typeof val === 'object' ? JSON.stringify(val) : String(val);
                                    localStorage.setItem(key, strVal);
                                    sessionStorage.setItem(key, strVal);
                                    
                                    // Also set camelCase variants just in case
                                    const camelKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
                                    if (camelKey !== key) {
                                        localStorage.setItem(camelKey, strVal);
                                        sessionStorage.setItem(camelKey, strVal);
                                    }
                                }
                                
                                // Write Okta Auth SDK standard key layout ("okta-token-storage")
                                if (token) {
                                    const oktaStorage = JSON.stringify({
                                        accessToken: {
                                            accessToken: token,
                                            tokenType: "Bearer",
                                            scopes: ["openid", "email", "profile"],
                                            claims: payload
                                        },
                                        idToken: {
                                            idToken: token,
                                            claims: payload
                                        }
                                    });
                                    localStorage.setItem('okta-token-storage', oktaStorage);
                                    sessionStorage.setItem('okta-token-storage', oktaStorage);
                                    
                                    // Write consolidated nested session objects
                                    const sessionObj = JSON.stringify({
                                        token: token,
                                        access_token: token,
                                        accessToken: token,
                                        tokenType: "Bearer",
                                        ...payload
                                    });
                                    
                                    const nestedKeys = [
                                        'user', 'auth', 'token_details', 'credentials', 
                                        'user_session', 'session', 'auth_data', 'authData'
                                    ];
                                    for (const nKey of nestedKeys) {
                                        localStorage.setItem(nKey, sessionObj);
                                        sessionStorage.setItem(nKey, sessionObj);
                                    }
                                }
                            }
                        }""", [raw_token_val, jwt_payload])
                    except Exception:
                        pass # Ignore initial redirection/load interruptions

                # 3. Re-navigate to load the actual protected page contents with active token fully loaded
                try:
                    await page.goto(url, timeout=20000, wait_until="load")
                except Exception as goto_err:
                    try:
                        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    except Exception as fallback_err:
                        await context.close()
                        await browser.close()
                        raise RuntimeError(f"Failed to load website {url}: {str(fallback_err)}")

                # Wait for Next.js router compilation, MSAL handshakes, and chat bots layout rendering to fully complete!
                wait_time = 8000 if raw_token_val else 1000
                await page.wait_for_timeout(wait_time)

                target_filename = f"{name}.png"
                target_filepath = os.path.join(base_folder, target_filename)
                
                # Perform FULL PAGE screenshot capture to dynamically render scrolling canvases
                await page.screenshot(path=target_filepath, full_page=True)
                captured_paths[name] = target_filepath

            await context.close()
            await browser.close()
        return captured_paths

    async def setup_baseline(self, name: str, url: str, db: Session, access_token: str = None) -> dict:
        """
        Creates a baseline visual model, takes desktop/tablet/mobile snaps inside a Proactor thread,
        and registers details in SQLite.
        """
        # 1. Create Baseline instance
        baseline = Baseline(name=name, url=url)
        db.add(baseline)
        db.flush()

        # Build clean directory structure: static/baselines/{id}/
        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        
        try:
            # 2. Capture baseline screenshots in our isolated Proactor thread
            captured_files = run_async_in_new_thread(self._capture_screenshots(url, baseline_folder, access_token))
            
            # 3. Save BaselineScreenshot entries
            for viewport, path in captured_files.items():
                # Store relative paths for easier static serving across hosts
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
            # Clean up files created prior to rollback
            if os.path.exists(baseline_folder):
                import shutil
                shutil.rmtree(baseline_folder, ignore_errors=True)
            raise e

    async def run_regression_test(self, run_id: int, db: Session, access_token: str = None):
        """
        Executes comparison screenshot capture inside a Proactor thread and runs CV visual subtraction.
        Updates state of RegressionTestRun record on completion or failure.
        """
        run = db.query(RegressionTestRun).filter(RegressionTestRun.id == run_id).first()
        if not run:
            return

        run.status = "running"
        db.commit()

        run_folder = os.path.join(self.static_dir, "runs", str(run.id))
        
        try:
            # 1. Capture snapshots of the new target URL inside our isolated Proactor thread
            target_snaps = run_async_in_new_thread(self._capture_screenshots(run.target_url, run_folder, access_token))
            
            # 2. Extract baseline screenshot files
            baseline = db.query(Baseline).filter(Baseline.id == run.baseline_id).first()
            if not baseline or not baseline.screenshots:
                raise ValueError(f"Baseline {run.baseline_id} does not contain screenshots.")

            baseline_map = {s.viewport: s.image_path for s in baseline.screenshots}

            mismatch_count = 0
            viewports_run = 0

            # 3. Compare each viewport using OpenCV
            for viewport, run_filepath in target_snaps.items():
                base_rel_path = baseline_map.get(viewport)
                if not base_rel_path:
                    continue
                
                base_filepath = os.path.join(self.static_dir, base_rel_path)
                diff_filename = f"diff_{viewport}.png"
                diff_filepath = os.path.join(run_folder, diff_filename)

                # Execute Image Comparison
                similarity, is_mismatch = self._compare_images(
                    baseline_path=base_filepath,
                    run_path=run_filepath,
                    diff_output_path=diff_filepath
                )

                if is_mismatch:
                    mismatch_count += 1

                # Save relative paths to DB
                run_rel_path = os.path.relpath(run_filepath, self.static_dir).replace("\\", "/")
                diff_rel_path = os.path.relpath(diff_filepath, self.static_dir).replace("\\", "/")

                test_result = RegressionTestResult(
                    run_id=run.id,
                    viewport=viewport,
                    similarity_score=similarity,
                    baseline_image_path=base_rel_path,
                    run_image_path=run_rel_path,
                    diff_image_path=diff_rel_path,
                    is_mismatch=is_mismatch
                )
                db.add(test_result)
                viewports_run += 1

            # 4. Record summary data
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
        """
        Deletes baseline record from SQLite (cascading test runs/results automatically),
        and safely cleans up all baseline and runs screenshot subfolders from disk.
        """
        baseline = db.query(Baseline).filter(Baseline.id == baseline_id).first()
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} does not exist.")

        baseline_name = baseline.name
        import shutil
        
        # 1. Delete physical baseline folder on disk
        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        if os.path.exists(baseline_folder):
            shutil.rmtree(baseline_folder, ignore_errors=True)
            
        # 2. Delete physical runs folders associated with this baseline
        for run in baseline.runs:
            run_folder = os.path.join(self.static_dir, "runs", str(run.id))
            if os.path.exists(run_folder):
                shutil.rmtree(run_folder, ignore_errors=True)

        # 3. Delete database record (cascades Related BaselineScreenshots, RegressionTestRuns, and RegressionTestResults)
        db.delete(baseline)
        db.commit()
        try:
            from app.routes.audit_logs import log_audit
            log_audit(db, "visual_testing", f"Permanently deleted visual baseline '{baseline_name}' and cleared all associated comparison runs.")
        except Exception:
            pass

    async def recapture_baseline(self, baseline_id: int, db: Session, access_token: str = None) -> dict:
        """
        Launches Playwright in a Proactor thread, captures fresh screenshots of the baseline URL,
        overwrites the old visual benchmarks on disk, and updates DB modified timestamp.
        """
        baseline = db.query(Baseline).filter(Baseline.id == baseline_id).first()
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} does not exist.")

        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        
        # 1. Take fresh screenshot captures (automatically overwrites old files on disk!)
        captured_files = run_async_in_new_thread(self._capture_screenshots(baseline.url, baseline_folder, access_token))
        
        # 2. Update created_at timestamp to reflect fresh synchronization
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
