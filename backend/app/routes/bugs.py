import os
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import BugReport
from app.services.bug_reporter import BugReporterService

router = APIRouter(prefix="/api/bug-reporter", tags=["Bug Reporter Assistant"])
bug_service = BugReporterService()

# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class BugExportRequest(BaseModel):
    target: str # 'jira', 'azure_devops', 'github', 'gitlab'
    credentials: Dict[str, Any]


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
    file: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(""),
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Ingest an optional visual layout screenshot and user details, pipe it to an LLM Vision/Text auditor,
    and output a detailed, structured bug assessment compatible with market-wide trackers (Jira, DevOps).
    """
    if not x_llm_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API Key is missing. Please enter it in your Settings panel."
        )

    # If both file and description are blank, raise an error
    if not file and not description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least a screenshot file or a text description context."
        )

    try:
        image_bytes = None
        filename = None
        
        # Parse uploaded screenshot if provided
        if file and file.filename:
            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file must be a valid image format."
                )
            image_bytes = await file.read()
            filename = file.filename
        result = await bug_service.analyze_screenshot_bug(
            image_bytes=image_bytes,
            filename=filename,
            user_description=description,
            provider=x_llm_provider,
            model=x_llm_model,
            api_key=x_llm_api_key,
            db=db
        )
        return result
    except Exception as err:
        import traceback
        print("\n=== BUG ANALYZE EXCEPTION ENCOUNTERED ===")
        traceback.print_exc()
        print("===========================================\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze bug request: {str(err)}"
        )


@router.post("/export/{bug_id}", response_model=dict)
async def export_bug_to_tracker(
    bug_id: int,
    payload: BugExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export an audited drafted bug report to the user's selected issue tracker (Jira, DevOps, GitHub, GitLab) dynamically.
    """
    bug = db.query(BugReport).filter(BugReport.id == bug_id).first()
    if not bug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bug Report with ID {bug_id} not found."
        )

    target = payload.target.lower().strip()
    creds = payload.credentials

    try:
        if target == "jira":
            return await bug_service.export_to_jira(
                bug=bug,
                jira_domain=creds.get("jira_domain"),
                jira_email=creds.get("jira_email"),
                jira_token=creds.get("jira_token"),
                jira_project=creds.get("jira_project"),
                db=db
            )
        elif target == "azure_devops":
            return await bug_service.export_to_azure_devops(
                bug=bug,
                organization=creds.get("organization"),
                project=creds.get("project"),
                personal_access_token=creds.get("personal_access_token"),
                db=db
            )
        elif target == "github":
            return await bug_service.export_to_github(
                bug=bug,
                owner=creds.get("owner"),
                repo=creds.get("repo"),
                personal_access_token=creds.get("personal_access_token"),
                db=db
            )
        elif target == "gitlab":
            return await bug_service.export_to_gitlab(
                bug=bug,
                project_id=creds.get("project_id"),
                personal_access_token=creds.get("personal_access_token"),
                db=db
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported bug tracking target platform: {target}"
            )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(err)}"
        )


@router.post("/test-connection", response_model=dict)
async def test_tracker_connection(payload: BugExportRequest):
    """
    Test connection to the selected bug tracker platform dynamically to verify credentials, domains, and tokens.
    """
    target = payload.target.lower().strip()
    creds = payload.credentials
    
    try:
         result = await bug_service.test_connection(target=target, creds=creds)
         return result
    except Exception as e:
         import traceback
         print("\n=== TRACKER CONNECTION TEST EXCEPTION ===")
         traceback.print_exc()
         print("==========================================\n")
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=str(e)
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
