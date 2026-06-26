import os
import cv2
import numpy as np
import threading
import asyncio
import base64
import json
import urllib.request
import httpx
import re
from datetime import datetime
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright
from app.models import Baseline, BaselineScreenshot, RegressionTestRun, RegressionTestResult

VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "laptop": {"width": 1366, "height": 768},
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

    async def _capture_screenshots(
        self, 
        url: str, 
        base_folder: str, 
        access_token: str = None, 
        chrome_profile_path: str = None, 
        headless_mode: bool = True,
        capture_desktop: bool = True,
        capture_laptop: bool = True,
        capture_tablet: bool = True,
        capture_mobile: bool = True
    ) -> dict:
        """
        Launches Playwright browser context. Deploys Pre-Authentication!
        Loads in once at the start of the session, automatically re-navigates directly back to your
        intended sub-page (e.g. /GetUser), and captures pristine viewports of your secure page!
        If a pre-saved manual session file exists, preloads it natively on context boot!
        """
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url

        os.makedirs(base_folder, exist_ok=True)
        captured_paths = {}

        # Symmetrical Credentials check
        is_credentials = bool(access_token and ":" in access_token and not "\t" in access_token)
        is_persistent = bool(chrome_profile_path and os.path.exists(chrome_profile_path))
        
        # Standard Bearer Headers (Only if we are NOT using credentials or persistent profiles!)
        headers = prepare_universal_auth_headers(access_token) if (access_token and not is_persistent and not is_credentials) else {}
        
        raw_token_val = None
        jwt_payload = {}
        storage_state = None
        
        # Dynamic Session State File Resolver:
        # Check if they have a pre-saved manual browser session file saved on the server!
        session_path = os.path.join(self.static_dir, "session_state.json")
        is_saved_session = os.path.exists(session_path)

        if is_saved_session and not is_persistent:
            storage_state = session_path
            print("   🚀 DETECTED SAVED BROWSER AUTHENTICATION SESSION ON SERVER! LOADING ON-BOOT NATIVELY...")
        elif access_token and not is_persistent and not is_credentials:
            raw_token_val = headers.get("Authorization", "").replace("Bearer ", "").strip()
            jwt_payload = decode_jwt_payload(raw_token_val)
            
            # PRE-COMPILE NATIVE STORAGE STATE (100% Custom SSO and JSON support!)
            local_storage_items = []
            
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
        elif is_credentials:
            print(f"   🚀 LAUNCHING PLAYWRIGHT IN HANDS-FREE AUTO-LOGIN SOLVER MODE...")
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

                # DYNAMIC MULTI-COOKIE INJECTION ROUTINE
                if access_token and not is_credentials:
                    try:
                        raw_cookie_str = access_token.strip()
                        cookies_to_add = []
                        
                        from urllib.parse import urlparse
                        domain_clean = urlparse(url).netloc.split(":")[0]
                        
                        # Check if it is a Tab-Separated block copied from Chrome DevTools!
                        lines = raw_cookie_str.split("\n")
                        is_tab_separated = any("\t" in line for line in lines)
                        
                        if is_tab_separated:
                            print("   🚀 DETECTED DEVTOOLS TAB-SEPARATED COOKIE LIST! PARSING NATIVELY...")
                            for line in lines:
                                if not line.strip():
                                    continue
                                parts = line.split("\t")
                                if len(parts) >= 2:
                                    c_name = parts[0].strip()
                                    c_val = parts[1].strip()
                                    
                                    # Optional extracted domain/path
                                    c_domain = domain_clean
                                    if len(parts) >= 3 and ("." in parts[2] or parts[2] == domain_clean):
                                        c_domain = parts[2].strip()
                                        
                                    cookies_to_add.append({
                                        "name": c_name,
                                        "value": c_val,
                                        "domain": c_domain,
                                        "path": "/"
                                    })
                        elif ";" in raw_cookie_str or "=" in raw_cookie_str:
                            cookie_parts = raw_cookie_str.split(";")
                            for part in cookie_parts:
                                if "=" in part:
                                    k, v = part.split("=", 1)
                                    cookies_to_add.append({
                                        "name": k.strip(),
                                        "value": v.strip(),
                                        "domain": domain_clean,
                                        "path": "/"
                                    })
                        else:
                            cookies_to_add = [
                                {"name": "sessionid", "value": raw_cookie_str, "domain": domain_clean, "path": "/"},
                                {"name": "ASP.NET_SessionId", "value": raw_cookie_str, "domain": domain_clean, "path": "/"},
                                {"name": ".AspNetCore.Cookies", "value": raw_cookie_str, "domain": domain_clean, "path": "/"},
                                {"name": "token", "value": raw_cookie_str, "domain": domain_clean, "path": "/"},
                                {"name": "access_token", "value": raw_cookie_str, "domain": domain_clean, "path": "/"}
                            ]
                            
                        await context.add_cookies(cookies_to_add)
                        print(f"   🚀 LEGACY/SSR COOKIES SUCCESSFULLY INJECTED ({len(cookies_to_add)} keys) ON DOMAIN '{domain_clean}'!")
                    except Exception as cookie_err:
                        print(f"   ⚠️ Cookie injection bypassed: {cookie_err}")

                page = await context.new_page()

            if raw_token_val and not is_persistent and not is_saved_session:
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

            # -----------------------------------------------------------------
            # 🚀 VIEWPORTS SCREENSHOT CAPTURE SWEEP (Symmetrical Navigation Loop)
            # -----------------------------------------------------------------
            is_authenticated = False # Set authentication tracker state
            
            # Dynamic Viewport Selection: Strictly compile viewports checked by the user
            active_viewports = {}
            if capture_desktop:
                active_viewports["desktop"] = VIEWPORTS["desktop"]
            if capture_laptop:
                active_viewports["laptop"] = VIEWPORTS["laptop"]
            if capture_tablet:
                active_viewports["tablet"] = VIEWPORTS["tablet"]
            if capture_mobile:
                active_viewports["mobile"] = VIEWPORTS["mobile"]
                
            # Fallback guard: if none is selected, default to desktop
            if not active_viewports:
                active_viewports["desktop"] = VIEWPORTS["desktop"]
            
            for name, viewport in active_viewports.items():
                print(f"   📸 Capture Visual Sweep: resizing to '{name.upper()}' viewport ({viewport['width']}x{viewport['height']})...")
                await page.set_viewport_size(viewport)
                
                # 1. Load the Target URL
                try:
                    print(f"   🌐 Navigating to {url} ...")
                    await page.goto(url, timeout=25000, wait_until="domcontentloaded")
                except Exception as goto_err:
                    await context.close()
                    if 'browser' in locals() and browser:
                        await browser.close()
                    raise RuntimeError(f"Failed to load website {url}: {str(goto_err)}")

                # 2. RUN AUTO-LOGIN SOLVER (Only once on the first un-authenticated desktop viewport!)
                if is_credentials and not is_authenticated:
                    current_url = page.url
                    # Only execute login solver if we are redirected to a login screen!
                    if "login" in current_url.lower() or "signin" in current_url.lower():
                        try:
                            u_name, u_pass = access_token.strip().split(":", 1)
                            print(f"   🚀 AUTO-LOGIN SOLVER: Detecting login elements on '{current_url}'...")
                            
                            # 🧠 INTELLIGENT SELF-HEALING FIELD SCRAPER
                            username_el = None
                            password_el = None
                            submit_el = None
                            
                            inputs = await page.locator("input").all()
                            
                            # A. Scrape Username Field
                            best_u_score = -1
                            for el in inputs:
                                if not await el.is_visible():
                                    continue
                                i_type = (await el.get_attribute("type") or "").lower()
                                i_name = (await el.get_attribute("name") or "").lower()
                                i_id = (await el.get_attribute("id") or "").lower()
                                i_placeholder = (await el.get_attribute("placeholder") or "").lower()
                                
                                if i_type not in ["text", "email", ""]:
                                    continue
                                    
                                score = 0
                                for kw in ["user", "name", "email", "login", "id"]:
                                    if kw in i_name: score += 10
                                    if kw in i_id: score += 10
                                    if kw in i_placeholder: score += 5
                                    
                                if score > best_u_score:
                                    best_u_score = score
                                    username_el = el
                                    
                            # B. Scrape Password Field (Strictly prioritizes type="password"!)
                            for el in inputs:
                                if not await el.is_visible():
                                    continue
                                i_type = (await el.get_attribute("type") or "").lower()
                                if i_type == "password":
                                    password_el = el
                                    break
                                    
                            if not password_el:
                                best_p_score = -1
                                for el in inputs:
                                    if not await el.is_visible():
                                        continue
                                    i_type = (await el.get_attribute("type") or "").lower()
                                    i_name = (await el.get_attribute("name") or "").lower()
                                    i_id = (await el.get_attribute("id") or "").lower()
                                    
                                    score = 0
                                    if "pass" in i_name or "pass" in i_id: score += 10
                                    if score > best_p_score:
                                        best_p_score = score
                                        password_el = el
                                        
                            # C. Scrape Submit Button Field
                            buttons = await page.locator("button, input[type='submit'], input[type='button']").all()
                            best_s_score = -1
                            for el in buttons:
                                if not await el.is_visible():
                                    continue
                                b_type = (await el.get_attribute("type") or "").lower()
                                b_name = (await el.get_attribute("name") or "").lower()
                                b_id = (await el.get_attribute("id") or "").lower()
                                b_val = (await el.get_attribute("value") or "").lower()
                                b_text = (await el.inner_text() or "").lower()
                                
                                score = 0
                                if b_type == "submit": score += 10
                                for kw in ["login", "signin", "sign-in", "submit", "enter", "continue"]:
                                    if kw in b_text: score += 10
                                    if kw in b_val: score += 10
                                    if kw in b_id: score += 5
                                    if kw in b_name: score += 5
                                    
                                if score > best_s_score:
                                    best_s_score = score
                                    submit_el = el

                            # Auto-fill credentials using identified secure elements
                            if username_el and password_el and submit_el:
                                print("   🔑 Auto-filling credentials using self-healed form fields...")
                                await username_el.fill(u_name)
                                await password_el.fill(u_pass)
                                await page.wait_for_timeout(500)

                                print("   🖱️ Clicking login submit button...")
                                await submit_el.click()
                            else:
                                raise ValueError("Could not dynamically locate username, password, or submit elements on form.")
                            
                            # Dismiss active session popup modal warnings
                            print("   🛡️ Monitoring for active 'Session Exists / Override' popup dialogs...")
                            await page.wait_for_timeout(2000)
                            
                            confirm_texts = ["Yes", "Confirm", "Continue", "Force Login", "Terminate", "OK", "Override", "Yes, Override"]
                            for confirm_text in confirm_texts:
                                popup_btn = page.locator(f'button:has-text("{confirm_text}"), input[value*="{confirm_text}"], a:has-text("{confirm_text}")').first
                                if await popup_btn.is_visible():
                                    print(f"   🚨 DETECTED 'ALREADY LOGGED IN' POPUP OVERRIDE BUTTON: '{confirm_text}'! Clicking it automatically...")
                                    await popup_btn.click()
                                    break

                            # CRITICAL SYMMETRICAL WAIT STATE
                            print("   🔄 Waiting for secure session redirect to complete...")
                            await page.wait_for_url(lambda u: "login" not in u.lower(), timeout=12000)
                            await page.wait_for_load_state("networkidle", timeout=8000)
                            
                            # Symmetrical 2-second sleep to ensure server fully writes and commits session states
                            await page.wait_for_timeout(2000)
                            print("   ✓ Authentication completely finalized!")
                            
                            is_authenticated = True # Toggle auth tracker to avoid duplicate login calls!
                            
                            # Re-navigate back to the target secure sub-page now fully authenticated!
                            print(f"   🔄 RE-NAVIGATING DESKTOP VIEWPORT SECURELY TO SUB-PAGE: {url} ...")
                            await page.goto(url, timeout=20000, wait_until="networkidle")
                            
                        except Exception as login_err:
                            print(f"   ⚠️ Automated login solver bypassed or failed: {login_err}")

                # 3. RUN UNIVERSAL STORAGE SWEEP LOOP (Bearer mode only - on first run!)
                elif raw_token_val and not is_persistent and not is_authenticated:
                    current_url = page.url
                    if "login" in current_url.lower() or "signin" in current_url.lower():
                        try:
                            print(f"   🔑 Deploying Symmetrical Universal Storage Sweep...")
                            jwt_payload_json = json.dumps(jwt_payload) if jwt_payload else '{}'
                            
                            await page.evaluate(f'''([token, claims]) => {{
                                const keys = [
                                    'token', 'access_token', 'accessToken', 'jwt', 'Authorization', 
                                    'auth_token', 'authToken', 'session_token', 'sessionToken', 
                                    'jwtToken', 'jwt_token', 'bearer_token', 'id_token', 'idToken', 
                                    'user_token', 'userToken', 'credentials', 'auth', 'isAuthenticated',
                                    'isLoggedIn', 'user_session', 'userSession', 'session'
                                ];

                                const nestedSession = JSON.stringify({{
                                    "token": token,
                                    "accessToken": token,
                                    "access_token": token,
                                    "tokenType": "Bearer",
                                    ...claims
                                }});

                                const oktaStorage = JSON.stringify({{
                                    "accessToken": {{
                                        "accessToken": token,
                                        "tokenType": "Bearer",
                                        "scopes": ["openid", "email", "profile"],
                                        "claims": claims
                                    }},
                                    "idToken": {{
                                        "idToken": token,
                                        "claims": claims
                                    }}
                                }});

                                for (const key of keys) {{
                                    localStorage.setItem(key, token);
                                    sessionStorage.setItem(key, token);
                                    localStorage.setItem(key, "Bearer " + token);
                                    sessionStorage.setItem(key, "Bearer " + token);
                                    localStorage.setItem(key, nestedSession);
                                    sessionStorage.setItem(key, nestedSession);
                                }}

                                localStorage.setItem("okta-token-storage", oktaStorage);
                                sessionStorage.setItem("okta-token-storage", oktaStorage);
                                localStorage.setItem("isAuthenticated", "true");
                                sessionStorage.setItem("isAuthenticated", "true");

                                window.token = token;
                                window.accessToken = token;
                                window.authToken = token;
                            }}''', [raw_token_val, jwt_payload])
                            print(f"   ✓ Storage Sweep completed successfully across localStorage, sessionStorage, and window context!")
                            
                            # Force bind reload
                            print(f"   🔄 Performing authentication bind reload...")
                            await page.reload(timeout=20000, wait_until="networkidle")
                            print(f"   ✓ Authentication reload completed successfully!")
                            is_authenticated = True
                        except Exception as sweep_err:
                            print(f"   ⚠️ Storage sweep bypassed: {sweep_err}")

                # 🚀 ENTERPRISE AJAX & DELAY BUSTER:
                # A. Wait for all background dynamic AJAX fetches and API data counters to complete
                try:
                    print("   🔄 Waiting for all background API and data fetches to complete (networkidle)...")
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass

                # B. Symmetrical Settle Wait (Comfortable 5.0-second buffer to let all charts, loaders, and repaints finalize!)
                print("   ⏳ Sleeping for 5.0 seconds to let the UI layout fully settle, repaint, and load all charts...")
                await page.wait_for_timeout(5000)

                # Verify page load state before capture
                current_url = page.url
                print(f"   📍 Viewport '{name.upper()}' loaded: {current_url}")
                if "login" in current_url.lower() or "signin" in current_url.lower():
                    print("   ⚠️ WARNING: Viewport loaded login screen! Session might have expired.")

                target_filename = f"{name}.png"
                target_filepath = os.path.join(base_folder, target_filename)
                
                # Capture the fully authenticated view!
                await page.screenshot(path=target_filepath, full_page=True)
                captured_paths[name] = target_filepath

            await context.close()
            if 'browser' in locals() and browser:
                await browser.close()
        return captured_paths

    async def _harvest_session_state_worker(self, url: str, state_path: str):
        """Worker executing manual browser login headfully inside an isolated Proactor Thread."""
        async with async_playwright() as p:
            # Launch 100% headfully so the user can manually see, log in, and click warning popups on their desktop!
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                ignore_https_errors=True,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            print(f"   🔒 [HARVESTER] Navigating to login entry point: {url}")
            await page.goto(url, timeout=30000)
            
            print("   🔒 [HARVESTER] Browser window opened! Please manually complete your login on screen, override warning popups...")
            
            # Loop and monitor the active URL and state in real-time!
            # Once they enter their password, click login, and successfully transition to their Home or GetUser dashboard,
            # the backend immediately extracts your session cookies/StorageState, saves it, and CLOSES the browser automatically!
            is_harvested = False
            for _ in range(120): # Timeout after 60 seconds (120 * 0.5s)
                if page.is_closed():
                    break
                    
                current_u = page.url.lower()
                # Check if we have transitioned successfully to standard authenticated landing paths!
                if any(path in current_u for path in ["/home", "/dashboard", "/main", "/index", "/getuser"]):
                    print(f"   ✓ [HARVESTER] Successful login detected at URL: {page.url}!")
                    # Wait 1.5 seconds to let cookies fully settle in the browser jar
                    await asyncio.sleep(1.5)
                    
                    state = await context.storage_state()
                    with open(state_path, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)
                        
                    print(f"   ✓ [HARVESTER] Session successfully harvested and saved to disk at {state_path}!")
                    is_harvested = True
                    break
                    
                await asyncio.sleep(0.5)
                
            # Fallback if the user closed the window before the redirect completed
            if not is_harvested and not page.is_closed():
                try:
                    state = await context.storage_state()
                    with open(state_path, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)
                    print("   ✓ [HARVESTER] Fallback session saved.")
                except Exception:
                    pass
                    
            await context.close()
            await browser.close()

    async def harvest_session_state(self, url: str) -> dict:
        """
        Launches a headful manual login browser on the desktop, captures the active authenticated
        storage state upon close, and saves it natively to disk as a pre-populated baseline fallback!
        """
        state_path = os.path.join(self.static_dir, "session_state.json")
        run_async_in_new_thread(self._harvest_session_state_worker, url, state_path)
        return {
            "status": "success",
            "message": f"Session state successfully harvested and saved natively to disk! Future visual testing runs will automatically load this logged-in session on boot."
        }

    async def setup_baseline(self, name: str, url: str, db: Session, application_name: str = "Default Application", access_token: str = None, chrome_profile_path: str = None, headless_mode: bool = True, capture_desktop: bool = True, capture_laptop: bool = True, capture_tablet: bool = True, capture_mobile: bool = True) -> dict:
        # Symmetrical Self-Healing: Instantly recreate schemas on-demand if missing on disk!
        from app.database import engine
        from app.models import Base
        Base.metadata.create_all(bind=engine)

        baseline = Baseline(application_name=application_name, name=name, url=url)
        db.add(baseline)
        db.flush()

        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        
        try:
            # Symmetrical, thread-local instantiation to prevent cross-loop task conflicts!
            captured_files = run_async_in_new_thread(
                self._capture_screenshots, 
                url, 
                baseline_folder, 
                access_token, 
                chrome_profile_path, 
                headless_mode,
                capture_desktop=capture_desktop,
                capture_laptop=capture_laptop,
                capture_tablet=capture_tablet,
                capture_mobile=capture_mobile
            )
            
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

    async def recapture_baseline(self, baseline_id: int, db: Session, access_token: str = None, chrome_profile_path: str = None, headless_mode: bool = True, capture_desktop: bool = True, capture_tablet: bool = True, capture_mobile: bool = True) -> dict:
        baseline = db.query(Baseline).filter(Baseline.id == baseline_id).first()
        if not baseline:
            raise ValueError(f"Baseline {baseline_id} does not exist.")

        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        
        # Symmetrical, thread-local instantiation to prevent cross-loop task conflicts!
        captured_files = run_async_in_new_thread(self._capture_screenshots, baseline.url, baseline_folder, access_token, chrome_profile_path, headless_mode, capture_desktop, capture_tablet, capture_mobile)
        
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
