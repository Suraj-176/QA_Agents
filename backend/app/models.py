from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

# =====================================================================
# AGENT 1: SMART REGRESSION TESTING MODELS
# =====================================================================

class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    screenshots = relationship("BaselineScreenshot", back_populates="baseline", cascade="all, delete-orphan")
    runs = relationship("RegressionTestRun", back_populates="baseline", cascade="all, delete-orphan")


class BaselineScreenshot(Base):
    __tablename__ = "baseline_screenshots"

    id = Column(Integer, primary_key=True, index=True)
    baseline_id = Column(Integer, ForeignKey("baselines.id", ondelete="CASCADE"), nullable=False)
    viewport = Column(String, nullable=False) # 'desktop', 'tablet', 'mobile'
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    baseline = relationship("Baseline", back_populates="screenshots")


class RegressionTestRun(Base):
    __tablename__ = "regression_test_runs"

    id = Column(Integer, primary_key=True, index=True)
    baseline_id = Column(Integer, ForeignKey("baselines.id", ondelete="CASCADE"), nullable=False)
    target_url = Column(String, nullable=False)
    status = Column(String, default="pending") # 'pending', 'running', 'completed', 'failed'
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    baseline = relationship("Baseline", back_populates="runs")
    results = relationship("RegressionTestResult", back_populates="run", cascade="all, delete-orphan")


class RegressionTestResult(Base):
    __tablename__ = "regression_test_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("regression_test_runs.id", ondelete="CASCADE"), nullable=False)
    viewport = Column(String, nullable=False) # 'desktop', 'tablet', 'mobile'
    similarity_score = Column(Float, nullable=True) # Percentage similarity, e.g., 99.5
    baseline_image_path = Column(String, nullable=False)
    run_image_path = Column(String, nullable=False)
    diff_image_path = Column(String, nullable=True)
    is_mismatch = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    run = relationship("RegressionTestRun", back_populates="results")


# =====================================================================
# AGENT 2: TEST CASE GENERATOR MODELS
# =====================================================================

class RequirementSource(Base):
    __tablename__ = "requirement_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    suites = relationship("TestCaseSuite", back_populates="requirement", cascade="all, delete-orphan")


class TestCaseSuite(Base):
    __tablename__ = "test_case_suites"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirement_sources.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    requirement = relationship("RequirementSource", back_populates="suites")
    test_cases = relationship("TestCase", back_populates="suite", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_case_suites.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(String, nullable=False) # TC-001, TC-002, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    preconditions = Column(Text, nullable=True)
    steps = Column(JSON, nullable=False) # JSON list of strings/steps
    expected_result = Column(Text, nullable=False)
    priority = Column(String, nullable=False) # High, Medium, Low
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    suite = relationship("TestCaseSuite", back_populates="test_cases")


# =====================================================================
# AGENT 3: BUG REPORT ASSISTANT MODELS
# =====================================================================

class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False) # Critical, High, Medium, Low
    screenshot_path = Column(String, nullable=True)
    annotated_screenshot_path = Column(String, nullable=True)
    jira_key = Column(String, nullable=True) # e.g., PROJ-123
    jira_url = Column(String, nullable=True)
    status = Column(String, default="draft") # 'draft', 'submitted_to_jira'
    ai_analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
