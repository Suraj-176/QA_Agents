# QA.AI Platform — Decoupled, Multi-Agent Smart QA Assistant

Welcome to the **QA.AI Platform**! This is a state-of-the-art, platform-agnostic, and Docker-free quality assurance engine designed to supercharge visual regression testing, automated test case development, and dynamic bug tracking. 

Built using a highly modular **FastAPI (Python)** backend and an elegant **Vite + React (TypeScript/JavaScript)** frontend, the application is completely decoupled and runs with **zero-friction local setups**.

---

## 🏗️ System Architecture & Modularity

The application enforces a strict separation of concerns, ensuring each agent operates inside isolated packages without coupling.

```
QA.AI Platform/
├── backend/                       ← Python FastAPI Core
│   ├── app/
│   │   ├── database.py           ← Agnostic SQLite connection pools
│   │   ├── models.py             ← Relational schema tables (Agent 1, 2, 3)
│   │   ├── routes/
│   │   │   ├── regression.py     ← API routes for Agent 1 (Visual Agent)
│   │   │   ├── test_cases.py     ← API routes for Agent 2 (Test Cases)
│   │   │   ├── bugs.py           ← API routes for Agent 3 (Bug Reporter)
│   │   │   └── automation.py     ← API routes for Agent 4 (Automation)
│   │   ├── services/
│   │   │   ├── regression_testing.py  ← Agent 1 Logic (Playwright + OpenCV)
│   │   │   ├── test_case_generator.py ← Agent 2 Logic (Requirements extraction)
│   │   │   ├── bug_reporter.py        ← Agent 3 Logic (LLM Vision + Jira Exporter)
│   │   │   ├── automation_agent.py    ← Agent 4 Logic (3-Step Scaffolding Engine)
│   │   │   └── llm_adapter.py         ← Unified multi-LLM router (BYOK)
│   │   └── main.py               ← App entry point, self-healing db, & static mounts
│   ├── requirements.txt           ← Python dependencies
│   └── tests/                     ← 14 Comprehensive automated unit tests
│
└── frontend/                      ← Vite + React + Tailwind CSS
    ├── src/
    │   ├── components/            ← Clean, high-fidelity tab modules
    │   │   ├── Dashboard.jsx
    │   │   ├── RegressionModule.jsx
    │   │   ├── TestCaseModule.jsx
    │   │   ├── BugReporterModule.jsx
    │   │   ├── AutomationModule.jsx
    │   │   └── Settings.jsx
    │   └── App.jsx                ← Workspace router & sidebar layout
    ├── package.json
    └── tailwind.config.js
```

---

## 🧠 Dynamic "Bring Your Own Key" (BYOK) Security

This application implements a secure, privacy-first **BYOK pattern**:
1. **Zero Server Storage:** No LLM API Keys or JIRA credentials are saved in the backend SQLite database.
2. **Browser Sandbox:** Credentials are input into the **Configuration Panel** and saved exclusively inside the browser's local sandbox storage (`localStorage`).
3. **Provider-Isolated Key Schema:** Keys and models are isolated per provider (e.g. `llm_openai_api_key`, `llm_gemini_api_key`) to prevent key-bleeding completely.
4. **Transient Headers:** Every transaction transmits keys dynamically using secure headers. The backend instantiates the requested client for *that request only* and discards the credentials immediately.
5. **SSO Token Security (.gitignore):** Your dynamic manual session file `static/session_state.json` (containing active corporate cookies) and traceback log directories are automatically untracked and ignored by Git, shielding your organization completely!

---

## 🛠️ The Four Core AI Agents

### 🔍 Agent 1: Smart Visual Regression Testing (Upgraded!)
* **Engine:** Playwright (Python) + OpenCV (Computer Vision).
* **4-Viewport Captures:** Captures and compares layouts across Desktop (`1920x1080`), **Laptop (`1366x768`)** 💻, Tablet (`768x1024`), and Mobile (`375x667`) viewports.
* **📂 Multi-App Grouped Baselines:** Real-time folder-level grouping (`📂 TruBI v2` etc.) with capsule counts. Supports selective, parallel folder-level automation sweeps!
* **🔐 Live Manual Session Harvester:** Opens headful desktop Chrome, busters duplicate-session warnings, and extracts your active cookies under matched, strict User-Agent signatures to bypass anti-session-hijacking firewalls perfectly.
* **🏎️ 0ms Zero-Token AI Triage:** Completely bypasses duplicate Gemini Vision API calls! Clicking "AI Triage" reads and renders your pre-calculated layout audit from the local SQLite database in 0ms!

### 📋 Agent 2: AI TestCase Generator (Upgraded!)
* **Engine:** Multi-LLM adapter (Gemini API, OpenAI, Anthropic Claude, OpenRouter).
* **Workflow:** Processes unstructured requirements, user stories, or functional constraints, dynamically engineering comprehensive happy-path and edge-case testing plans formatted cleanly into SQLite tables and exportable as Excel CSV sheets.

### 🐛 Agent 3: Vision-Based Bug Reporter & Exporter (Upgraded!)
* **Engine:** LLM Vision + Atlassian JIRA Cloud / DevOps REST APIs.
* **Workflow:** Drag-and-drop a screenshot of a broken page, enter comments, and let the AI Vision model perform an audit (isolating overlaps, missing assets, raw exceptions), ready for 1-click publishing to Jira, Azure DevOps, GitLab, or GitHub with visual attachments!

### 🏗️ Agent 4: Automation Architect (New!)
* **Engine:** 3-Step Foundation Generation Pipeline.
* **Workflow:** Bootstraps full, production-ready Selenium, Playwright, or Cypress test automation frameworks in TypeScript or Python.
* **📦 Clean Architecture Suffixes:** Dynamically packages ZIP archives using short, cache-busting suffixes (e.g. `bootstrap_playwright_typescript_bdd_5a2b.zip`) to prevent browser cache blocks while keeping filenames highly professional!

---

## 🚀 Docker-Free Local Quick Start (Less than 2 Minutes)

This project has been engineered to run out-of-the-box on Windows, macOS, or Linux without requiring Docker, Postgres, or Redis!

### 🐍 1. Spin up the Python Backend
Open a terminal in the root directory:
```bash
# Move to backend
cd backend

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Playwright browser drivers
playwright install chromium

# Launch the server (runs on http://127.0.0.1:5000)
python main.py
```

### ⚛️ 2. Spin up the React Frontend
In a new terminal window:
```bash
# Move to frontend
cd frontend

# Install node dependencies
npm install

# Start Vite live workspace (runs on http://127.0.0.1:3000)
npm run dev
```

Open `http://127.0.0.1:3000` in your web browser, enter your API Keys in the **Configuration Panel**, and begin testing immediately!

---

## 🧹 Automatic 7-Day Log Pruner
The backend is equipped with an automated SQLite transaction pruner. Every time a new action is logged, the platform calculates 7 days ago and permanently purges any logs older than 7 days, maintaining a high-performance, self-healing database index hands-free!

---

## 🧪 Running Automated Unit Tests
To verify API states, visual subtraction formulas, and relational cascades, execute:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m unittest discover tests
```
