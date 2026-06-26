# 🐞 Agent 3: Vision-Based Bug Reporter Guide

Welcome! This agent helps you automatically translate visual application defects, layout errors, or general functional bugs into professional, structured reports, and publish them to JIRA or Azure DevOps with a single click.

---

## 🚀 Step-by-Step Instructions

### Step 1: Upload a Screenshot or Describe the Bug
You can submit a bug in two different ways:
*   **Method A (Visual Audit - Recommended):** 
    Drag-and-drop or upload a screenshot of your broken page directly into the dashed box. Enter some quick context remarks (e.g. `Checkout page overlapping on Chrome`).
*   **Method B (Text-Only Bug):** 
    If you don't have a screenshot, leave the box blank, and simply describe your bug context inside the text area.

---

### Step 2: Audit and Draft
1. Click the green **Audit and Draft Bug** button.
2. The system sends your files and remarks to your connected LLM Vision model.
3. The AI performs an automated multimodal layout audit and returns:
   - **A Professional Title:** (e.g. `Overlapping action buttons block checkout submission on widescreen viewports`).
   - **Structured Description:** An exhaustive outline containing Screen Positions, Affected Viewports, and Expected vs. Actual styles.
   - **Steps to Reproduce:** An ordered step-by-step reproduction sequence.
   - **Expected Result & Severity Rating:** Evaluated according to visual and functional severity rules.

---

### Step 3: Configure Your Bug Tracker Connection
To publish your drafted bugs directly into your corporate board:
1. Click **⚙️ Configuration Panel** in your sidebar.
2. Go to **Enterprise Bug Tracker Integrations** card.
3. Select your target (e.g. `Jira Cloud` or `Azure DevOps`).
4. Enter your host URL domain, your account email, and your Personal Access API Token.
5. Click **Save Bug Tracker Credentials** to lock your settings.

---

### Step 4: Publish to JIRA/DevOps (In 1 Click!)
1. Go back to **🐞 Visual Bug Reporter**.
2. Select your drafted bug report from your history sidebar on the left.
3. Click the blue **Publish to Connected Tracker** button.
4. **Watch the magic happen:** The platform connects to JIRA, creates the actual ticket, maps severity and priorities, and uploads your screenshot as a physical JIRA file attachment automatically!
5. *The button turns into a green confirmation link—click "View Ticket" to open and manage your newly created issue ticket in your browser instantly!*
