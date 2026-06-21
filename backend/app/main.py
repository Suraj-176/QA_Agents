import os
import sys
import asyncio

# Fix Windows asyncio NotImplementedError for Playwright subprocesses inside Uvicorn/FastAPI
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app import models # Explicitly load all tables into Metadata before table creation
from app.routes import regression, test_cases, bugs

# Initialize directory for storing screenshots and visual diffs
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Automatically create all SQLite tables on application startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QA.AI Platform API Server",
    description="Decoupled, multi-agent AI assistant for visual regression testing, test case generation, and bug reporting.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all origins for cross-platform local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file system to serve visual baselines and diff results
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# Register routers
app.include_router(regression.router)
app.include_router(test_cases.router)
app.include_router(bugs.router)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "QA.AI Platform Core Server",
        "supported_agents": [
            "Smart Visual Regression Testing (Agent 1)",
            "Dynamic LLM Test Case Generator (Agent 2)",
            "Multi-Modal JIRA Bug Reporter (Agent 3)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True)
