from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.services.automation_agent import AutomationAgentService

router = APIRouter(prefix="/api/automation", tags=["Automation Architect"])
automation_service = AutomationAgentService()

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
        if v not in ["Playwright", "Selenium"]:
            raise ValueError("Supported tools are strictly 'Playwright' or 'Selenium'.")
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
        traceback.print_exc()  # Prints the complete python traceback to Uvicorn terminal logs!
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
        result = automation_service.write_file_to_framework(
            folder_path=payload.folder_path,
            relative_path=payload.relative_path,
            code=payload.code,
            db=db
        )
        return result
    except Exception as err:
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
