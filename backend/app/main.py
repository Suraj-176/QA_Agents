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
from app.routes import regression, test_cases, bugs, audit_logs, automation

# Initialize directory for storing screenshots and visual diffs
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Automatically create all SQLite tables on application startup
Base.metadata.create_all(bind=engine)

# Symmetrical database dynamic migration support!
# Adds the 'ai_analysis' column to 'regression_test_results' dynamically if missing.
from app.database import SessionLocal
from sqlalchemy import text
_db = SessionLocal()
try:
    _db.execute(text("ALTER TABLE regression_test_results ADD COLUMN ai_analysis TEXT"))
    _db.commit()
    print("   🛠️ SQLite Dynamic Schema Migration: Added 'ai_analysis' column successfully!")
except Exception:
    # Ignore if column already exists (sqlite raises exception on duplicates)
    pass
finally:
    _db.close()

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
app.include_router(audit_logs.router)
app.include_router(automation.router)

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


from pydantic import BaseModel
from fastapi import HTTPException
from typing import Optional

class TestConnectionRequest(BaseModel):
    provider: str
    model: str
    api_key: str
    azure_endpoint: Optional[str] = None
    azure_api_version: Optional[str] = None

@app.post("/api/settings/test-connection")
async def test_llm_connection(payload: TestConnectionRequest):
    """
    Validates that the provided LLM credentials, model name, and provider are correct
    by executing a lightweight, non-destructive API ping in the background.
    """
    from app.services.llm_adapter import LLMAdapter
    from app.routes.automation import write_to_platform_txt_log
    try:
        # Log connection test attempt
        write_to_platform_txt_log(
            message=f"LLM Connection Test initiated. Provider: {payload.provider.upper()}, Model: '{payload.model}', Endpoint: '{payload.azure_endpoint or 'N/A'}'"
        )

        # A simple, ultra-fast, and cheap ping question
        ping_prompt = "Respond with exactly the single word: OK"
        response = await LLMAdapter.generate_text(
            provider=payload.provider,
            model=payload.model,
            api_key=payload.api_key,
            prompt=ping_prompt,
            azure_endpoint=payload.azure_endpoint,
            azure_api_version=payload.azure_api_version
        )
        if "OK" in response.upper() or len(response) > 0:
            write_to_platform_txt_log(
                message=f"LLM Connection Test SUCCESS. Connected to {payload.provider.upper()}!"
            )
            return {
                "status": "success",
                "message": f"Successfully connected to {payload.provider.upper()}! Credentials and model '{payload.model}' are validated."
            }
        else:
            raise ValueError(f"Provider did not respond with expected ping token. Raw Response: {response}")
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        print(tb_str)
        
        # Write exact traceback to our persistent logs/platform_logs.txt!
        write_to_platform_txt_log(
            message=f"LLM Connection Test FAILED for {payload.provider.upper()}: {str(e)}",
            error_traceback=tb_str
        )
        
        raise HTTPException(
            status_code=400,
            detail=f"Connection test failed for {payload.provider.upper()}: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True)
