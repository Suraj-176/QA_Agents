from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.services.automation_agent import AutomationAgentService

router = APIRouter(prefix="/api/automation", tags=["Automation Architect"])
automation_service = AutomationAgentService()

# =====================================================================
# PERSISTENT LOCAL TXT LOGGING HELPER
# =====================================================================

def write_to_platform_txt_log(message: str, error_traceback: str = None, raw_llm_response: str = None):
    """
    Saves traceable platform executions, detailed tracebacks, and raw LLM responses
    directly into a local persistent 'backend/logs/platform_logs.txt' file on disk.
    """
    import os
    from datetime import datetime
    
    try:
        # Configure absolute path to backend/logs/platform_logs.txt
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file_path = os.path.join(logs_dir, "platform_logs.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n====================================================================\n")
            f.write(f"⏰ TIMESTAMP: {timestamp}\n")
            f.write(f"📝 MESSAGE: {message}\n")
            
            if error_traceback:
                f.write(f"--------------------------------------------------------------------\n")
                f.write(f"🚨 EXCEPTION TRACEBACK:\n{error_traceback}\n")
                
            if raw_llm_response:
                f.write(f"--------------------------------------------------------------------\n")
                f.write(f"🔮 RAW LLM RESPONSE:\n{raw_llm_response}\n")
                
            f.write(f"====================================================================\n")
    except Exception as e:
        print(f"Failed to write to persistent log file: {e}")


# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class BootstrapRequest(BaseModel):
    tool: str  # 'Playwright' or 'Selenium'
    language: str  # 'JavaScript', 'TypeScript', 'Python', 'Java'
    pattern: Optional[str] = "Standard POM"  # 'Standard POM', 'BDD (Cucumber / Gherkin)', 'Data-Driven (CSV/JSON Inputs)'
    output_folder: Optional[str] = None  # Made Optional to support pure ZIP-only web downloads!

    @validator('tool')
    def validate_tool(cls, v):
        if v not in ["Playwright", "Selenium", "Cypress"]:
            raise ValueError("Supported tools are strictly 'Playwright', 'Selenium', or 'Cypress'.")
        return v

    @validator('language')
    def validate_language(cls, v):
        if v not in ["JavaScript", "TypeScript", "Python", "Java"]:
            raise ValueError("Supported languages are 'JavaScript', 'TypeScript', 'Python', or 'Java'.")
        return v

    @validator('pattern')
    def validate_pattern(cls, v):
        allowed = [
            "BDD (Cucumber / Gherkin)", 
            "Data-Driven (CSV/JSON Inputs)", 
            "API-First Hybrid Testing", 
            "Keyword-Driven Testing",
            "Standard POM"
        ]
        if v not in allowed:
            raise ValueError(f"Supported patterns are strictly: {', '.join(allowed)}")
        return v

    @validator('output_folder')
    def validate_output_folder(cls, v):
        if v is None:
            return None
        return v.strip()


class FileGenRequest(BaseModel):
    folder_path: str
    instruction: str

    @validator('folder_path')
    def validate_folder_path(cls, v):
        if not v or not v.strip():
            raise ValueError("folder_path cannot be empty.")
        return v.strip()

    @validator('instruction')
    def validate_instruction(cls, v):
        if not v or not v.strip():
            raise ValueError("instruction details cannot be empty.")
        return v.strip()


class WriteFileRequest(BaseModel):
    folder_path: str
    relative_path: str
    code: str


# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
async def bootstrap_framework(
    payload: BootstrapRequest,
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Bootstrap a complete, clean, and production-ready automated testing framework from scratch
    at the specified local directory, and packages a .zip archive for fast downloads.
    """
    if not x_llm_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key is missing. Please configure it in your Settings panel."
        )

    try:
        # Log scaffolding initiation in our local persistent log file
        write_to_platform_txt_log(
            message=f"Initiated framework scaffolding. Tool: {payload.tool}, Language: {payload.language}, Pattern: {payload.pattern}, Destination: {payload.output_folder or 'ZIP-Only'}"
        )

        result = await automation_service.bootstrap_framework(
            tool=payload.tool,
            language=payload.language,
            pattern=payload.pattern or "Standard POM",
            output_folder=payload.output_folder,
            provider=x_llm_provider,
            model=x_llm_model,
            api_key=x_llm_api_key,
            db=db
        )
        return result
    except Exception as err:
        import traceback
        tb_str = traceback.format_exc()
        print(tb_str)  # Print to terminal console
        
        # Write exact traceback to our persistent logs/platform_logs.txt!
        write_to_platform_txt_log(
            message=f"Automation bootstrapping failed: {str(err)}",
            error_traceback=tb_str
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automation bootstrapping failed: {str(err)}"
        )


@router.post("/generate")
async def generate_framework_file(
    payload: FileGenRequest,
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Scan an existing local framework context, learn its patterns, and generate a new code file
    (such as a Page Object model, API helper, or test spec) cleanly matching their style.
    """
    if not x_llm_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key is missing. Please configure it in your Settings panel."
        )

    try:
        # Log generation initiation in our local persistent log file
        write_to_platform_txt_log(
            message=f"Initiated file generation extender. Folder: {payload.folder_path}, Instruction: '{payload.instruction}'"
        )

        result = await automation_service.generate_framework_file(
            folder_path=payload.folder_path,
            user_instruction=payload.instruction,
            provider=x_llm_provider,
            model=x_llm_model,
            api_key=x_llm_api_key,
            db=db
        )
        return result
    except Exception as err:
        import traceback
        tb_str = traceback.format_exc()
        print(tb_str)  # Print to terminal console
        
        # Capture raw LLM output if present inside exception message
        raw_resp = None
        if "Raw Response:" in str(err):
            parts = str(err).split("Raw Response:\n")
            if len(parts) > 1:
                raw_resp = parts[1]
        
        # Write exact traceback and raw LLM response to our persistent logs/platform_logs.txt!
        write_to_platform_txt_log(
            message=f"Code generation failed: {str(err)}",
            error_traceback=tb_str,
            raw_llm_response=raw_resp
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(err)}"
        )


@router.post("/write")
async def write_file_to_framework(payload: WriteFileRequest, db: Session = Depends(get_db)):
    """
    Saves a generated code block directly as a physical file onto your local framework directory.
    """
    try:
        # Log write initiation in our local persistent log file
        write_to_platform_txt_log(
            message=f"Initiated file write operation. Folder: {payload.folder_path}, Destination Path: '{payload.relative_path}'"
        )

        result = automation_service.write_file_to_framework(
            folder_path=payload.folder_path,
            relative_path=payload.relative_path,
            code=payload.code,
            db=db
        )
        return result
    except Exception as err:
        import traceback
        tb_str = traceback.format_exc()
        print(tb_str)  # Print to terminal console
        
        # Write exact traceback to our persistent logs/platform_logs.txt!
        write_to_platform_txt_log(
            message=f"Failed to write file to framework: {str(err)}",
            error_traceback=tb_str
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to framework: {str(err)}"
        )


@router.get("/browse-folder")
async def browse_local_folder():
    """
    Launches a native Windows directory picker dialog on the host OS using Tkinter,
    and returns the selected absolute physical directory path to the frontend.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Withdraw main tkinter window
        root.attributes("-topmost", True)  # Force dialog to topmost level on Windows desktop
        
        selected_dir = filedialog.askdirectory(
            title="Select Local Automation Framework Folder",
            initialdir="C:\\"
        )
        root.destroy()
        
        normalized_path = selected_dir.replace("\\", "/") if selected_dir else ""
        return {"folder_path": normalized_path}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to launch native folder browser: {str(e)}"
        )
