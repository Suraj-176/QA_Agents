from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Baseline, RegressionTestRun, RegressionTestResult
from app.services.regression_testing import RegressionTestingService

router = APIRouter(prefix="/api/regression-testing", tags=["Regression Testing"])
regression_service = RegressionTestingService()

# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class BaselineCreateRequest(BaseModel):
    name: str
    url: str


class TestRunRequest(BaseModel):
    baseline_id: int
    target_url: str


class ScreenshotSchema(BaseModel):
    viewport: str
    image_path: str

    class Config:
        from_attributes = True


class BaselineResponseSchema(BaseModel):
    id: int
    name: str
    url: str
    created_at: str
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
    created_at: str
    results: List[ResultResponseSchema]

    class Config:
        from_attributes = True


# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.post("/baselines", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_baseline(payload: BaselineCreateRequest, db: Session = Depends(get_db)):
    """
    Establish a visual baseline by launching Playwright and capturing desktop, tablet, and mobile views.
    """
    try:
        result = await regression_service.setup_baseline(
            name=payload.name,
            url=payload.url,
            db=db
        )
        return result
    except Exception as err:
        import traceback
        print("\n=== BASELINE CREATION EXCEPTION ENCOUNTERED ===")
        traceback.print_exc()
        print("===============================================\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create visual baseline screenshots: {str(err)}"
        )


@router.get("/baselines", response_model=List[BaselineResponseSchema])
async def list_baselines(db: Session = Depends(get_db)):
    """
    Retrieve all established visual baselines.
    """
    baselines = db.query(Baseline).all()
    results = []
    for b in baselines:
        results.append({
            "id": b.id,
            "name": b.name,
            "url": b.url,
            "created_at": b.created_at.isoformat(),
            "screenshots": b.screenshots
        })
    return results


@router.post("/test", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def run_regression_test(
    payload: TestRunRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Trigger a visual regression test against an established baseline. Runs as a non-blocking background task.
    """
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
        target_url=payload.target_url,
        status="pending"
    )
    db.add(run)
    db.commit()

    # Enqueue comparison routine on FastAPI's native asyncio BackgroundTasks worker queue
    background_tasks.add_task(
        regression_service.run_regression_test,
        run_id=run.id,
        db=db
    )

    return {
        "run_id": run.id,
        "status": "pending",
        "message": "Visual regression comparison job successfully scheduled and running in background."
    }


@router.get("/runs/{run_id}", response_model=RunDetailResponseSchema)
async def get_run_details(run_id: int, db: Session = Depends(get_db)):
    """
    Retrieve execution state, text summaries, and viewport diff results for a visual comparison run.
    """
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
        "created_at": run.created_at.isoformat(),
        "results": run.results
    }
