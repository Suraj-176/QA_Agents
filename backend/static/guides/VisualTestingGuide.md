# 🔍 Agent 1: Smart Visual Regression Testing Guide

Welcome! This agent helps you automatically inspect your application's layout, buttons, alignments, and fonts across 4 different screen sizes (Desktop, Laptop, Tablet, Mobile) without doing any manual checks. It points out exactly what changed by highlighting differences in red.

---

## 🚀 Step-by-Step Instructions

### Step 1: Capture your Corporate Login Session (Once)
If your application requires entering a username and password, you must capture a login session first:
1. Click **⚙️ Configuration Panel** in your left-hand sidebar.
2. Scroll to the bottom and click the glowing **🔐 Capture Live Session** button.
3. Enter your application's Login URL (e.g., `http://192.168.4.187/TruBI25v2Rel/Account/Login`) and click OK.
4. **A browser window will pop up on your desktop!**
5. Manually log in with your credentials on the screen.
6. Once you successfully land on your Home dashboard page, **the window will automatically close itself!**
7. Your session is now saved securely on your local computer.

---

### Step 2: Establish Your Approved Visual Baseline
Before comparing pages, you must take a "Baseline" screenshot of how the page *should* look when it is correct:
1. Click **🔍 Smart Visual testing** in the left-hand sidebar.
2. In the **Establish New Base** form:
   - **Application Name (Optional):** Enter your project name (e.g., `TruBI v2`). This groups your pages cleanly in folders!
   - **Baseline Name:** Enter a description (e.g., `User Manager`).
   - **URL:** Enter the secure sub-page URL you want to test (e.g., `http://192.168.4.187/TruBI25v2Rel/Admin/usermanager/GetUser`).
3. Click the green **Capture Baseline** button.
4. Wait 5 seconds. The browser runs in the background, bypasses your login wall using your saved session cookies, waits for data charts to fetch, and snaps your approved viewports!

---

### Step 3: Run Visual Regression Comparisons
When developers update the code, you can verify if anything broke in the layout:
1. Select your target baseline page from your grouped folder list in the left-hand sidebar.
2. In the **Compare Base** form on the right, enter your comparison target URL (default is your baseline URL).
3. Click the green **Run Comparison** button.
4. The system will take a new background screenshot and compare it against your baseline.
5. If there are any differences (margins shifted, text clipped, buttons wrapped, overlapping cards), **the mismatches will be highlighted with a red overlay map!**

---

### Step 4: Run AI Visual Triage Analysis (In 1 Click!)
If any layout regressions are found:
1. Click the glowing **AI Triage** button underneath the broken viewport.
2. An **Instant AI Visual Triage modal will pop up on your screen!**
3. It will render a detailed, non-technical, bulleted layout report detailing:
   - **📐 Layout & Alignment Shifts:** How many pixels elements shifted.
   - **🎨 Styling & Typography Regressions:** Broken borders, font shifts, color violations.
   - **♿ Accessibility Observations:** Grey-on-white WCAG contrast problems.
   - **💡 Recommended Fix:** The exact CSS code your developers need to copy-paste to fix the layout instantly!
