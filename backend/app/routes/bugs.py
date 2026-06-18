import os
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import BugReport
from app.services.bug_reporter import BugReporterService

router = APIRouter(prefix="/api/bug-reporter", tags=["Bug Reporter Assistant"])
bug_service = BugReporterService()

# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class JiraExportRequest(BaseModel):
    jira_domain: str
    jira_email: str
    jira_token: str
    jira_project: str


class BugReportResponseSchema(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    screenshot_path: Optional[str]
    jira_key: Optional[str]
    jira_url: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True


# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.post("/analyze", response_model=dict, status_code=status.HTTP_201_CREATED)
async def analyze_screenshot(
    file: UploadFile = File(...),
    description: Optional[str] = Form(""),
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Ingest a visual layout screenshot, pipe it to an LLM Vision auditor using transient keys,
    and output a detailed, structured bug assessment.
    """
    if not x_llm_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API Key is missing. Please enter it in your Settings panel."
        )

    # Validate uploaded file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image format."
        )

    try:
        # Read raw image bytes
        image_bytes = await file.read()
        
        result = await bug_service.analyze_screenshot_bug(
            image_bytes=image_bytes,
            filename=file.filename,
            user_description=description,
            provider=x_llm_provider,
            model=x_llm_model,
            api_key=x_llm_api_key,
            db=db
        )
        return result
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze screenshot: {str(err)}"
        )


@router.post("/export/{bug_id}", response_model=dict)
async def export_to_jira(
    bug_id: int,
    payload: JiraExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export an audited draft bug report to JIRA Cloud, automatically uploading its visual attachment.
    """
    try:
        result = await bug_service.export_to_jira(
            bug_report_id=bug_id,
            jira_domain=payload.jira_domain,
            jira_email=payload.jira_email,
            jira_token=payload.jira_token,
            jira_project=payload.jira_project,
            db=db
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Atlassian JIRA Cloud export failed: {str(err)}"
        )


@router.get("/reports", response_model=List[BugReportResponseSchema])
async def list_reports(db: Session = Depends(get_db)):
    """
    Retrieve a compiled history list of all analyzed visual bugs.
    """
    reports = db.query(BugReport).all()
    results = []
    for r in reports:
        results.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "severity": r.severity,
            "screenshot_path": r.screenshot_path,
            "jira_key": r.jira_key,
            "jira_url": r.jira_url,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        })
    return results


@router.get("/reports/{bug_id}", response_model=BugReportResponseSchema)
async def get_report_details(bug_id: int, db: Session = Depends(get_db)):
    """
    Retrieve structural visual audit details for a specific bug.
    """
    report = db.query(BugReport).filter(BugReport.id == bug_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug Report with ID {bug_id} not found."
        )

    return {
        "id": report.id,
        "title": report.title,
        "description": report.description,
        "severity": report.severity,
        "screenshot_path": report.screenshot_path,
        "jira_key": report.jira_key,
        "jira_url": report.jira_url,
        "status": report.status,
        "created_at": report.created_at.isoformat()
    }


@router.delete("/reports/{bug_id}", status_code=status.HTTP_200_OK)
async def delete_bug_report(bug_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific bug audit from the database, and clean its screenshot image file from the disk.
    """
    report = db.query(BugReport).filter(BugReport.id == bug_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug Report with ID {bug_id} not found."
        )

    # Delete local screenshot file from disk if present
    if report.screenshot_path:
        full_screenshot_path = os.path.join(bug_service.static_dir, report.screenshot_path)
        if os.path.exists(full_screenshot_path):
            try:
                os.remove(full_screenshot_path)
            except Exception:
                pass

    db.delete(report)
    db.commit()
    return {"message": f"Successfully deleted Bug Report {bug_id}."}
