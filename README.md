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
│   │   │   ├── regression.py     ← API routes for Agent 1
│   │   │   ├── test_cases.py     ← API routes for Agent 2
│   │   │   └── bugs.py           ← API routes for Agent 3
│   │   ├── services/
│   │   │   ├── regression_testing.py  ← Agent 1 Logic (Playwright + OpenCV)
│   │   │   ├── test_case_generator.py ← Agent 2 Logic (Requirements extraction)
│   │   │   ├── bug_reporter.py        ← Agent 3 Logic (LLM Vision + Jira Exporter)
│   │   │   └── llm_adapter.py         ← Unified multi-LLM router (BYOK)
│   │   └── main.py               ← App entry point & static mounts
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
3. **Transient Headers:** Every transaction transmits keys dynamically using secure headers (`X-LLM-Provider`, `X-LLM-Model`, `X-LLM-API-Key`). The backend instantiates the requested client for *that request only* and discards the credentials immediately.

---

## 🛠️ The Three Core Agents

### 🔍 Agent 1: Smart Visual Regression Testing
* **Engine:** Playwright (Python) + OpenCV (Computer Vision).
* **Workflow:** Launches headless browsers to capture base page states across Desktop (`1920x1080`), Tablet (`768x1024`), and Mobile (`375x667`) viewports.
* **Review:** When target URLs are compared, OpenCV computes visual subtraction. If layout alignments shift or elements clip, a visual **red difference map overlay** is compiled and saved. Any layout similarity below `99.5%` triggers an automatic regression alarm.

### 📋 Agent 2: AI TestCase Generator
* **Engine:** Multi-LLM adapter (Gemini API, OpenAI, Anthropic Claude).
* **Workflow:** Processes unstructured functional user stories, constraints, or markdown requirements, dynamically engineering comprehensive happy-path and edge-case testing plans formatted cleanly into SQLite tables.

### 🐛 Agent 3: Vision-Based Bug Reporter & Jira Exporter
* **Engine:** LLM Vision (Gemini Vision, GPT-4o, Claude Sonnet) + JIRA Cloud REST APIs.
* **Workflow:** Drag-and-drop a screenshot of a broken page, enter manual comments, and let the AI Vision model perform a layout audit (isolating overlaps, unloaded graphics, raw exceptions).
* **Sync:** Publish your visual audit as a real ticket to JIRA with a single click. The script automatically creates the ticket, maps priority scales, and uploads the layout screenshot as a JIRA attachment.

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

## 🧪 Running Automated Unit Tests
To verify API states, visual subtraction formulas, and relational cascades, execute:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m unittest discover tests
```
