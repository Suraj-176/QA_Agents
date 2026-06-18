from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import TestCaseSuite, TestCase
from app.services.test_case_generator import TestCaseGeneratorService

router = APIRouter(prefix="/api/test-cases", tags=["Test Case Generator"])
generator_service = TestCaseGeneratorService()

# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class GenerateRequest(BaseModel):
    requirements: str
    title: Optional[str] = None


class TestCaseResponseSchema(BaseModel):
    id: int
    test_id: str
    title: str
    description: str
    preconditions: Optional[str]
    steps: List[str]
    expected_result: str
    priority: str

    class Config:
        from_attributes = True


class SuiteDetailResponseSchema(BaseModel):
    id: int
    title: str
    requirement_id: Optional[int]
    created_at: str
    test_cases: List[TestCaseResponseSchema]


class SuiteListResponseSchema(BaseModel):
    id: int
    title: str
    created_at: str
    test_case_count: int


# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.post("/generate", response_model=dict)
async def generate_test_cases(
    payload: GenerateRequest,
    x_llm_provider: Optional[str] = Header("gemini", alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header("gemini-1.5-flash", alias="X-LLM-Model"),
    x_llm_api_key: Optional[str] = Header(None, alias="X-LLM-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Generate test cases dynamically using any specified LLM provider and credentials passed transiently.
    """
    if not x_llm_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key is missing. Please configure it in your Settings panel."
        )

    try:
        result = await generator_service.generate_suite_from_requirements(
            requirements_content=payload.requirements,
            title=payload.title,
            provider=x_llm_provider,
            model=x_llm_model,
            api_key=x_llm_api_key,
            db=db
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during generation: {str(err)}"
        )


@router.get("/suites", response_model=List[SuiteListResponseSchema])
async def list_suites(db: Session = Depends(get_db)):
    """
    Retrieve all generated test suites along with their total test case counts.
    """
    suites = db.query(TestCaseSuite).all()
    results = []
    for suite in suites:
        results.append({
            "id": suite.id,
            "title": suite.title,
            "created_at": suite.created_at.isoformat(),
            "test_case_count": len(suite.test_cases)
        })
    return results


@router.get("/suites/{suite_id}", response_model=SuiteDetailResponseSchema)
async def get_suite_details(suite_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full structural details of a specific test suite, including its individual test cases.
    """
    suite = db.query(TestCaseSuite).filter(TestCaseSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Suite with ID {suite_id} not found."
        )
    
    return {
        "id": suite.id,
        "title": suite.title,
        "requirement_id": suite.requirement_id,
        "created_at": suite.created_at.isoformat(),
        "test_cases": suite.test_cases
    }


@router.delete("/suites/{suite_id}", status_code=status.HTTP_200_OK)
async def delete_suite(suite_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific test suite from the database (cascades and deletes associated test cases automatically).
    """
    suite = db.query(TestCaseSuite).filter(TestCaseSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test Suite with ID {suite_id} not found."
        )
    
    db.delete(suite)
    db.commit()
    return {"message": f"Successfully deleted Test Suite {suite_id}."}
