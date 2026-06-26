import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, Header
from pydantic import BaseModel, validator, HttpUrl
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Baseline, RegressionTestRun, RegressionTestResult
from app.services.regression_testing import RegressionTestingService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/regression-testing",
    tags=["Regression Testing"],
    responses={500: {"description": "Internal server error"}}
)

regression_service = RegressionTestingService()


# =====================================================================
# PYDANTIC SCHEMAS (Validated API Boundary Models)
# =====================================================================

class BaselineCreateRequest(BaseModel):
    name: str
    url: HttpUrl
    
    @validator('name')
    def name_not_empty(cls, v):
        """Validate baseline name is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()


class TestRunRequest(BaseModel):
    baseline_id: int
    target_url: HttpUrl
    
    @validator('baseline_id')
    def baseline_id_positive(cls, v):
        """Validate baseline_id is positive"""
        if v <= 0:
            raise ValueError('baseline_id must be a positive integer')
        return v


class ScreenshotSchema(BaseModel):
    viewport: str
    image_path: str

    class Config:
        from_attributes = True


class BaselineResponseSchema(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime
    screenshots: List[ScreenshotSchema]

    class Config:
        from_attributes = True


class ResultResponseSchema(BaseModel):
    id: int
    viewport: str
    similarity_score: Optional[float]
    baseline_image_path: str
    run_image_path: str
    diff_image_path: Optional[str]
    is_mismatch: bool
    error_message: Optional[str]

    class Config:
        from_attributes = True


class RunDetailResponseSchema(BaseModel):
    id: int
    baseline_id: int
    target_url: str
    status: str
    summary: Optional[str]
    created_at: datetime
    results: List[ResultResponseSchema]

    class Config:
        from_attributes = True


# =====================================================================
# DEPENDENCY RESOLVER & TOKEN NORMALIZER
# =====================================================================

def extract_universal_access_token(
    x_access_token: Optional[str] = Header(None, alias="X-Access-Token"),
    x_browser_headers: Optional[str] = Header(None, alias="X-Browser-Headers")
) -> Optional[str]:
    """
    Universally extracts the active authentication token from incoming requests.
    Supports:
    1. X-Access-Token header directly (Curl Curls)
    2. X-Browser-Headers JSON/string configuration (React Settings UI Panel)
    """
    # 1. Prefer direct X-Access-Token
    if x_access_token and x_access_token.strip():
        return x_access_token.strip()
        
    # 2. Fallback and parse from X-Browser-Headers JSON / raw JWT string
    if x_browser_headers and x_browser_headers.strip():
        val = x_browser_headers.strip()
        
        # Parse JSON
        if val.startswith("{"):
            try:
                parsed = json.loads(val)
                # Look for standard token key names inside user JSON
                for key in ["Authorization", "authorization", "access_token", "accessToken", "token", "jwt"]:
                    if key in parsed:
                        return str(parsed[key]).strip()
            except Exception:
                pass
        
        # Return raw flat token string directly
        return val
        
    return None


# =====================================================================
# BACKGROUND TASK ERROR HANDLERS (With Transactional Safety)
# =====================================================================

async def run_regression_test_with_error_handling(
    run_id: int,
    db: Session,
    access_token: Optional[str] = None,
    chrome_profile_path: Optional[str] = None,
    headless_mode: bool = True,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    azure_api_version: Optional[str] = None
):
    """Executes comparison screenshots with complete error boundary isolation"""
    try:
        logger.info(f"Running comparison checks for run {run_id} ...")
        await regression_service.run_regression_test(
            run_id=run_id,
            db=db,
            access_token=access_token,
            chrome_profile_path=chrome_profile_path,
            headless_mode=headless_mode,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            azure_endpoint=azure_endpoint,
            azure_api_version=azure_api_version
        )
    except Exception as e:
        logger.error(f"Failed to execute background comparison run {run_id}: {str(e)}", exc_info=True)
        # Force fail state on db record to prevent hanging pending visual tests
        try:
            run = db.query(RegressionTestRun).filter(RegressionTestRun.id == run_id).first()
            if run:
                run.status = "failed"
                run.summary = f"Audit failed: {str(e)}"
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to record db failure for run {run_id}: {str(db_err)}")


# =====================================================================
# API ENDPOINTS (Token-Only General-Purpose Router)
# =====================================================================

@router.post(
    "/baselines",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create baseline visual screenshots"
)
async def create_baseline(
    payload: BaselineCreateRequest,
    access_token: Optional[str] = Depends(extract_universal_access_token),
    x_chrome_profile: Optional[str] = Header(None, alias="X-Chrome-Profile"),
    x_visual_headless: Optional[str] = Header("true", alias="X-Visual-Headless"),
    db: Session = Depends(get_db)
):
    """
    Establish a visual baseline by launching Playwright and capturing desktop, tablet, and mobile views.
    Works universally with ANY application using standard access token headers/cookies.
    """
    try:
        logger.info(f"Creating visual baseline benchmarks for '{payload.name}' at {payload.url} ...")
        headless_mode = (x_visual_headless != "false")
        result = await regression_service.setup_baseline(
            name=payload.name,
            url=str(payload.url),
            db=db,
            access_token=access_token,
            chrome_profile_path=x_chrome_profile,
            headless_mode=headless_mode
        )
        logger.info(f"✓ Baseline created successfully: ID {result.get('baseline_id')}")
        return result
    except Exception as err:
        logger.error(f"✗ Baseline creation failed: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create visual baseline screenshots: {str(err)}"
        )


@router.get(
    "/baselines",
    response_model=List[BaselineResponseSchema],
    summary="List all visual baselines"
)
async def list_baselines(db: Session = Depends(get_db)):
    """Retrieve all established visual baselines."""
    baselines = db.query(Baseline).all()
    results = []
    for b in baselines:
        results.append({
            "id": b.id,
            "name": b.name,
            "url": b.url,
            "created_at": b.created_at,
            "screenshots": b.screenshots
        })
    return results


@router.post(
    "/runs/all",
    response_model=Dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a global parallel visual regression test on all baselines"
)
async def run_all_regressions(
    background_tasks: BackgroundTasks,
    access_token: Optional[str] = Depends(extract_universal_access_token),
    x_chrome_profile: Optional[str] = Header(None, alias="X-Chrome-Profile"),
    x_visual_headless: Optional[str] = Header("true", alias="X-Visual-Headless"),
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    x_azure_endpoint: Optional[str] = Header(None, alias="X-Azure-Endpoint"),
    x_azure_api_version: Optional[str] = Header(None, alias="X-Azure-API-Version"),
    db: Session = Depends(get_db)
):
    """
    Launches an automated global visual regression sweep!
    Automatically loops through all baselines, enqueues parallel comparisons in the background,
    and returns a summary of scheduled runs instantly!
    """
    baselines = db.query(Baseline).all()
    if not baselines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No visual baselines established yet. Please create baselines first."
        )
        
    headless_mode = (x_visual_headless != "false")
    scheduled_runs = []
    
    for baseline in baselines:
        # Create a pending run for each baseline using its original URL as comparison target (or staging override)
        run = RegressionTestRun(
            baseline_id=baseline.id,
            target_url=baseline.url,
            status="pending"
        )
        db.add(run)
        db.commit()
        
        # Enqueue to background tasks list with complete pre-populated LLM variables!
        background_tasks.add_task(
            run_regression_test_with_error_handling,
            run_id=run.id,
            db=db,
            access_token=access_token,
            chrome_profile_path=x_chrome_profile,
            headless_mode=headless_mode,
            llm_provider=x_llm_provider,
            llm_model=x_llm_model,
            llm_api_key=x_llm_api_key,
            azure_endpoint=x_azure_endpoint,
            azure_api_version=x_azure_api_version
        )
        scheduled_runs.append({"run_id": run.id, "baseline": baseline.name})
        
    return {
        "status": "pending",
        "scheduled_count": len(scheduled_runs),
        "runs": scheduled_runs,
        "message": f"Successfully triggered parallel visual regressions for all {len(scheduled_runs)} established baselines in the background!"
    }


@router.post(
    "/test",
    response_model=Dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a visual regression test"
)
async def run_regression_test(
    payload: TestRunRequest,
    background_tasks: BackgroundTasks,
    access_token: Optional[str] = Depends(extract_universal_access_token),
    x_chrome_profile: Optional[str] = Header(None, alias="X-Chrome-Profile"),
    x_visual_headless: Optional[str] = Header("true", alias="X-Visual-Headless"),
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    x_azure_endpoint: Optional[str] = Header(None, alias="X-Azure-Endpoint"),
    x_azure_api_version: Optional[str] = Header(None, alias="X-Azure-API-Version"),
    db: Session = Depends(get_db)
):
    """Trigger a visual regression test. Runs as a non-blocking background task."""
    # Verify baseline exists
    baseline = db.query(Baseline).filter(Baseline.id == payload.baseline_id).first()
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline with ID {payload.baseline_id} does not exist."
        )

    # Create a pending test run entry
    run = RegressionTestRun(
        baseline_id=payload.baseline_id,
        target_url=str(payload.target_url),
        status="pending"
    )
    db.add(run)
    db.commit()

    headless_mode = (x_visual_headless != "false")

    # Enqueue comparison routine on FastAPI's background task queue with LLM details!
    background_tasks.add_task(
        run_regression_test_with_error_handling,
        run_id=run.id,
        db=db,
        access_token=access_token,
        chrome_profile_path=x_chrome_profile,
        headless_mode=headless_mode,
        llm_provider=x_llm_provider,
        llm_model=x_llm_model,
        llm_api_key=x_llm_api_key,
        azure_endpoint=x_azure_endpoint,
        azure_api_version=x_azure_api_version
    )

    logger.info(f"Scheduled visual regression comparison run {run.id}")
    return {
        "run_id": run.id,
        "status": "pending",
        "message": "Visual regression comparison job successfully scheduled and running in background."
    }


class SessionHarvestRequest(BaseModel):
    login_url: str


@router.post("/session/harvest", summary="Capture live browser session headfully")
async def harvest_browser_session(
    payload: SessionHarvestRequest,
    db: Session = Depends(get_db)
):
    """
    Launches a headful browser window on the user's desktop, allowing them to manually log in.
    Once they close the browser, automatically extracts and saves 100% of cookies and localStorage.
    """
    try:
        url_str = str(payload.login_url)
        logger.info(f"Initiating live session capture headfully for: {url_str} ...")
        
        # Call the harvesting service routine
        result = await regression_service.harvest_session_state(url_str)
        return result
    except Exception as err:
        logger.error(f"✗ Live session capture failed: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture live session state: {str(err)}"
        )


@router.post("/results/{result_id}/triage")
async def triage_visual_result(
    result_id: int,
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    x_azure_endpoint: Optional[str] = Header(None, alias="X-Azure-Endpoint"),
    x_azure_api_version: Optional[str] = Header(None, alias="X-Azure-API-Version"),
    db: Session = Depends(get_db)
):
    """
    Loads the OpenCV diff image and run image, and pipes them to Gemini Vision!
    Returns a rich, professional, written triage analysis detailing exactly what layout,
    alignment, color, or styling shifts occurred.
    """
    if not x_llm_api_key:
        raise HTTPException(status_code=400, detail="LLM API Key is missing in headers. Please check your settings.")
        
    result = db.query(RegressionTestResult).filter(RegressionTestResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Comparison result not found.")
        
    # Prioritize the OpenCV diff image as it highlights mismatches in red!
    img_path = result.diff_image_path if result.diff_image_path else result.run_image_path
    full_img_path = os.path.join(regression_service.static_dir, img_path)
    
    if not os.path.exists(full_img_path):
        raise HTTPException(status_code=404, detail="Visual screenshot file is missing from disk.")
        
    # Load prompt template
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "VisualTriagePrompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read().strip()
    except Exception:
        prompt_template = "Compare the baseline and run screenshot images and describe any visual errors."
        
    # Read image binary bytes
    with open(full_img_path, "rb") as image_file:
        image_bytes = image_file.read()
        
    try:
        from app.services.llm_adapter import LLMAdapter
        # Execute multimodal vision query!
        analysis_report = await LLMAdapter.analyze_image(
            provider=x_llm_provider,
            model=x_llm_model,
            api_key=x_llm_api_key,
            prompt=prompt_template,
            image_bytes=image_bytes,
            azure_endpoint=x_azure_endpoint,
            azure_api_version=x_azure_api_version
        )
        return {
            "result_id": result_id,
            "viewport": result.viewport,
            "similarity_score": result.similarity_score,
            "analysis": analysis_report
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Visual AI Triage failed: {str(e)}")


@router.get(
    "/runs/{run_id}",
    response_model=RunDetailResponseSchema,
    summary="Get visual regression test run details"
)
async def get_run_details(run_id: int, db: Session = Depends(get_db)):
    """Retrieve execution state and viewport diff results for a visual comparison run."""
    run = db.query(RegressionTestRun).filter(RegressionTestRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regression test run with ID {run_id} not found."
        )

    return {
        "id": run.id,
        "baseline_id": run.baseline_id,
        "target_url": run.target_url,
        "status": run.status,
        "summary": run.summary,
        "created_at": run.created_at,
        "results": run.results
    }


@router.delete(
    "/baselines/{baseline_id}",
    summary="Delete a baseline"
)
async def delete_baseline(baseline_id: int, db: Session = Depends(get_db)):
    """Delete a baseline and safely clean up all baseline and runs screenshot subfolders from disk."""
    try:
        await regression_service.delete_baseline(baseline_id=baseline_id, db=db)
        return {"message": f"Successfully deleted Baseline {baseline_id} and cleared related screenshot folders."}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@router.post(
    "/baselines/{baseline_id}/recapture",
    response_model=Dict[str, Any],
    summary="Recapture baseline screenshots"
)
async def recapture_baseline(
    baseline_id: int,
    access_token: Optional[str] = Depends(extract_universal_access_token),
    x_chrome_profile: Optional[str] = Header(None, alias="X-Chrome-Profile"),
    x_visual_headless: Optional[str] = Header("true", alias="X-Visual-Headless"),
    db: Session = Depends(get_db)
):
    """Re-capture and overwrite the visual viewport benchmarks for an established baseline URL."""
    try:
        headless_mode = (x_visual_headless != "false")
        result = await regression_service.recapture_baseline(
            baseline_id=baseline_id,
            db=db,
            access_token=access_token,
            chrome_profile_path=x_chrome_profile,
            headless_mode=headless_mode
        )
        logger.info(f"Successfully recaptured baseline {baseline_id}")
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recapture failed: {str(err)}"
        )
