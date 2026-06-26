# ⚙️ Configuration Panel & Security Master Guide

Welcome to the Security & Setup Core! This panel is the central nervous system of your QA AI Copilot. It operates on a privacy-first, secure, and completely dynamic architecture called **Bring Your Own Key (BYOK)**. 

---

## 🔒 1. How Our "Privacy-First" Security Architecture Works
To protect your sensitive company data, we enforce a strict zero-server storage policy:
1. **No Backend Database Storage:** Your API keys, personal access tokens (PATs), and JIRA passwords are **never** stored inside our local database. 
2. **Browser Sandbox:** When you input credentials, they are saved strictly inside your own browser's encrypted local storage (`localStorage`). They never leave your computer.
3. **Transient Headers:** Every time you click "Generate" or "Analyze", the React UI retrieves your keys from your browser's memory, transmits them securely inside dynamic HTTP headers to the local backend, which instantiates the requested AI client for *that request only* and discards your keys immediately.
4. **Zero Git Leaks:** Your manual session files (containing browser cookies) and log files are completely untracked and blocked by Git, keeping your organization 100% secure!

---

## 🧠 2. Card-by-Card Setup Instructions

### 📌 Section 1: Bring Your Own Key (BYOK)
This card connects your platform to your preferred generative AI cloud brain.
1. **LLM Cloud Provider Dropdown:** Select your preferred AI engine:
   *   **Google Gemini AI:** Best for fast visual triages and rich markdown descriptions.
   *   **OpenAI (GPT Engine):** Industry standard for complex, layered automation code scaffolding.
   *   **Azure OpenAI:** Enterprise-compliant Microsoft environment.
   *   **OpenRouter:** A unified gateway offering free access to models like `gemini-2.5-flash:free` or `llama-3.3-70b-instruct:free`.
2. **Selected Model:** Type the exact model string you wish to query (e.g. `gpt-4o` or `gemini-1.5-flash`).
3. **API Bearer Key:** Paste your secure cloud secret key. 
   - *💡 Tooltip Help: Click the Eye icon on the right to toggle key visibility!*
4. **Test LLM Connection:** Click this button before saving! The server will make a brief connection handshake to verify your key is active and display a green success banner!
5. **Save LLM Credentials:** Saves your selections to your browser sandbox.

---

### 📌 Section 2: Browser & Visual Testing Settings (Other Options)
This card configures how Playwright launches its browser engine to capture visual baselines.
1. **Custom Browser Session Headers (JSON Optional):**
   *   *Purpose:* If your corporate page is protected by a login screen, you can copy your active login headers (like `Authorization: Bearer token123`) from your Chrome DevTools (F12) and paste them here as a JSON block.
   *   *Action:* Playwright will automatically inject these headers on boot, bypassing your login walls instantly!
2. **🔐 Live Manual Session Harvester:**
   *   *Purpose:* If your application uses strict multi-factor authentication (MFA) or session-conflict overlays, copying headers might fail.
   *   *Action:* Click **Capture Live Session**, enter your portal's login page, manually log in on your desktop screen, bypass any warning dialogs, and land on your Home dashboard. **As soon as you succeed, the window will automatically close itself, harvest your active session cookies, and save them as a local bypass file!**
3. **Run Visual Testing Headless Toggle:**
   *   *Checked (Headless):* Playwright runs silently in the background (Fast).
   *   *Unchecked (Headful):* Opens an actual Google Chrome window visible on your desktop screen (Required if you are using manual browser session captures).
4. **Active Capture Viewports Settings:**
   *   *Action:* Check which viewports (Desktop, Laptop, Tablet, Mobile) you want to test. Unchecking unwanted viewports (like Tablet or Mobile) significantly speeds up baseline captures and saves local disk space!

---

### 📌 Section 3: Enterprise Bug Tracker Integrations
This card connects your platform to your project management boards to automate issue filings.
1. **Select Target Tracker:** Choose JIRA Cloud, Azure DevOps, GitHub, or GitLab.
2. **Jira Host Domain URL:** Enter your organization's JIRA URL (e.g. `https://my-org.atlassian.net`).
3. **Jira Account Email:** Enter your logging email address.
4. **Jira Project Access Key:** Enter your specific project identifier (e.g. `PROJ` or `DEV`).
5. **Jira API Token:** Paste your Personal JIRA API Token (generated from your Atlassian Security page).
6. **Test Tracker Connection:** Click this to verify JIRA is fully reachable before saving!

---

### 📌 Section 4: Prompts System Configuration Files
This card allows you to customize the core instructions used by our AI Agents in real-time.
1. **Select Prompt Target File:** Choose which agent prompt you want to modify (e.g. `VisualTriagePrompt.txt` or `BugReportPrompt.txt`).
2. **Prompt Template Editor:** The large text area will load your selected prompt's raw file directly from your hard drive! 
3. **Save Edited Prompt:** Writes your modified instructions directly back to your disk file. Future agent executions will instantly load your custom guidelines!
