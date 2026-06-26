# 🏗️ Agent 4: Automation Architect Guide

Welcome! This agent helps you automatically scaffold complete, production-ready, and enterprise-grade test automation repositories, and generate clean Page Object Model (POM) code scripts matching your custom code conventions.

---

## 🚀 Step-by-Step Instructions

### Step 1: Scaffold a Brand-New Framework Repository
To start a new testing project from scratch:
1. Click **🏗️ Automation Architect** in your left-hand sidebar.
2. Under **Configure Scaffolder**:
   - **Automation Tool:** Select your framework engine (e.g. `Playwright`, `Selenium`, or `Cypress`).
   - **Target Language:** Select your programming language (e.g. `TypeScript`, `JavaScript`, `Python`, or `Java`).
   - **Architecture Pattern:** Select your architectural template:
     *   `BDD (Cucumber / Gherkin)` (Saves files in .feature / steps folders)
     *   `Data-Driven` (Reads variables dynamically from local CSV/JSON files)
     *   `API-First Hybrid` (Uses API requests to bypass login gates)
   - **Local Scaffold Directory (Optional):** If you want to write the files directly onto your computer's hard drive, paste a path (e.g., `C:\QAAgents\my_new_framework`). Otherwise, leave it blank to download as a ZIP!
3. Click **Generate & Scaffold Framework**.
4. The system triggers three consecutive, deep-engineered LLM queries in the background to build your foundations, setup hooks, and login scenarios cleanly.
5. Click **Download Framework ZIP** to save and unpack your ready-to-test repository!

---

### Step 2: Extend Your Existing Framework with New Pages
If you already have a framework and want to write new pages or locator files:
1. Click the **🔧 Extend Existing Framework** tab at the top of your screen.
2. **Existing Framework Path:** Enter your framework's local path (e.g., `C:\QAAgents\my_new_framework`).
3. **Generation Instructions:** Describe what page object you want to build in plain English (e.g., `Create a BillingPage class. Add locator elements for creditCardInput ("#cc") and payBtn (".checkout"). Include an inputCardDetails(ccNum) helper function.`).
4. Click **Generate New File Code**.
5. **How it works:** The agent scans your local folders on disk, detects your imports, Page Object base classes, and async habits, and generates 100% custom, identical page scripts matching your style exactly!

---

### Step 3: Review and Save directly to disk
1. If the AI generated multiple files (like a cucumber feature file, a page locator class, and a step definition script), **use the Select File dropdown at the top of your preview to switch between them!**
2. You can click inside the code box and edit any characters on your keyboard manually.
3. Click the blue **Save to Disk** button.
4. **Watch the magic happen:** The platform surgically writes the file directly into your local hard drive at its exact output destination!
