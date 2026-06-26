# 📋 Agent 2: AI TestCase Generator Guide

Welcome! This agent helps you automatically translate plain-English functional requirements, user stories, and Jira tickets into a comprehensive, highly organized list of test cases, happy-path logic, validations, and edge cases.

---

## 🚀 Step-by-Step Instructions

### Step 1: Set Up your LLM Cloud Key
Since this agent is completely private, you must connect it to your own LLM Key:
1. Click **⚙️ Configuration Panel** in your left-hand sidebar.
2. Select your preferred provider (e.g. `Google Gemini AI` or `OpenAI`) and enter your private API Key.
3. Click the green **Save LLM Credentials** button.

---

### Step 2: Configure Your Generation Mode
1. Click **📋 Auto TestCase generator** in your left-hand sidebar.
2. In the **Generate Suite** form:
   - **Suite Title (Optional):** Enter a title for your test plans (e.g., `Checkout Card Validations`).
   - **Generation Mode Dropdown:** Select the specific focus of your test cases:
     *   **Combined (UI + Functional):** Generates test cases covering both visual layouts AND underlying business/database rules.
     *   **UI Only (Visual & Presentation):** Strictly focuses on responsive breakpoints, font clippings, colors, overlaps, and layout wrapping.
     *   **Functional Only (Logic & API):** Strictly focuses on API statuses, boundary inputs, data validations, and logical workflows.

---

### Step 3: Paste and Generate
1. In the large text area, paste your unstructured functional constraints, markdown specifications, or requirements copied directly from your Jira tickets.
2. Click the green **Generate Test Cases** button.
3. The platform streams your requirements to your connected AI model, parses its responses, repair truncated JSON formats dynamically in the background, and registers your test plan cleanly!

---

### Step 4: Explore and Export to Excel
1. Your test cases will load on screen inside a clean, high-contrast list!
2. Click on any test case row to expand its details:
   - **Test Objective:** The specific goal of the test.
   - **Preconditions:** The setup state required before starting.
   - **Action Steps:** A step-by-step ordered list of instructions to execute.
   - **Expected Outcome:** The successful behavior that must occur.
3. Click **Export to Excel (CSV)** at the top of your screen to download your complete test cases portfolio directly into a beautiful Excel sheet!
