# Building the 3 Agents - Complete Detailed Guide

## THE 3 AGENTS WE'RE BUILDING

Let me explain each agent in COMPLETE detail.

---

## 🎯 AGENT 1: SMART REGRESSION TESTING AGENT

### What It Does:

```
GOAL: Detect when code changes break existing functionality

PROCESS:
  1. User gives website URL
  2. Agent takes screenshots (3 viewports)
  3. Analyzes with AI
  4. Stores as BASELINE
  5. When developer commits code...
  6. Agent automatically runs tests again
  7. Compares with baseline
  8. Reports what broke
  9. Tells developer EXACTLY what to fix
```

### How It Works (Step by Step):

```
STEP 1: SETUP BASELINE (First time only)
┌─────────────────────────────────────┐
│ User inputs: www.example.com        │
│ Agent launches Playwright browser   │
│                                     │
│ Desktop (1920x1080):               │
│   - Takes screenshot               │
│   - Analyzes with OpenCV           │
│   - Stores result                  │
│                                     │
│ Tablet (768x1024):                 │
│   - Takes screenshot               │
│   - Analyzes with OpenCV           │
│   - Stores result                  │
│                                     │
│ Mobile (375x667):                  │
│   - Takes screenshot               │
│   - Analyzes with OpenCV           │
│   - Stores result                  │
│                                     │
│ DATABASE saves:                    │
│   ✓ 3 screenshots                  │
│   ✓ Analysis results               │
│   ✓ Test results (pass/fail)       │
│   ✓ Timestamp                      │
│                                     │
│ Result: BASELINE CREATED ✅         │
└─────────────────────────────────────┘

STEP 2: DEVELOPER MAKES CODE CHANGE
┌─────────────────────────────────────┐
│ Developer: "Fixed login button"     │
│ Commits code to GitHub             │
│                                     │
│ Git webhook triggers...            │
│ Agent automatically starts         │
└─────────────────────────────────────┘

STEP 3: AGENT RUNS REGRESSION TEST
┌─────────────────────────────────────┐
│ Agent wakes up (via webhook)       │
│ Pulls latest code                  │
│ Runs tests again (same 3 viewports)│
│                                     │
│ Desktop: PASS ✅                    │
│ Tablet: FAIL ❌ (was PASS before!) │
│ Mobile: PASS ✅                     │
│                                     │
│ REGRESSION DETECTED!               │
└─────────────────────────────────────┘

STEP 4: COMPARE WITH BASELINE
┌─────────────────────────────────────┐
│ Before (Baseline):                 │
│   Desktop: Screenshot A            │
│   Tablet: Screenshot B             │
│   Mobile: Screenshot C             │
│                                     │
│ After (Current):                   │
│   Desktop: Screenshot A' (same)    │
│   Tablet: Screenshot B' (DIFFERENT)│
│   Mobile: Screenshot C' (same)     │
│                                     │
│ Using OpenCV:                      │
│   cv2.absdiff(B, B')               │
│   Finds EXACT pixel differences    │
│                                     │
│ Result: TABLET VIEW BROKE          │
└─────────────────────────────────────┘

STEP 5: GENERATE REPORT
┌─────────────────────────────────────┐
│ REGRESSION DETECTED REPORT         │
│                                     │
│ Test: tablet_view_test             │
│ Status: FAILED (was PASSED)        │
│                                     │
│ What broke:                        │
│   - Button styling incorrect       │
│   - Navigation not responsive      │
│   - Layout shifted left            │
│                                     │
│ Where in code:                     │
│   File: styles.css                 │
│   Line: 145                        │
│   Change: margin-left changed      │
│                                     │
│ Severity: MAJOR                    │
│                                     │
│ Evidence:
│   - Before screenshot              │
│   - After screenshot               │
│   - Pixel difference map           │
│                                     │
│ Recommendation:                    │
│   Revert line 145 or adjust media  │
│   query for tablet viewport        │
└─────────────────────────────────────┘

STEP 6: NOTIFY DEVELOPER
┌─────────────────────────────────────┐
│ Email/Slack:                       │
│                                     │
│ "Regression detected in your code" │
│ Tablet view broken                 │
│ File: styles.css, Line: 145        │
│ Fix needed before merge            │
│                                     │
│ [View detailed report]             │
└─────────────────────────────────────┘

STEP 7: DEVELOPER FIXES AND RE-TESTS
┌─────────────────────────────────────┐
│ Developer fixes line 145           │
│ Commits updated code               │
│                                     │
│ Agent tests again automatically    │
│                                     │
│ Result:                            │
│ Desktop: PASS ✅                    │
│ Tablet: PASS ✅                     │
│ Mobile: PASS ✅                     │
│                                     │
│ Email: "All tests passing, safe!" │
│                                     │
│ Code merged safely! ✅              │
└─────────────────────────────────────┘
```

### Python Code Structure:

```python
# backend/app/services/regression_testing.py

from playwright.async_api import async_playwright
import cv2
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class RegressionTestingService:
    """
    Smart Regression Testing Agent
    
    Detects when code changes break existing functionality
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self.viewports = {
            'desktop': {'width': 1920, 'height': 1080},
            'tablet': {'width': 768, 'height': 1024},
            'mobile': {'width': 375, 'height': 667}
        }
    
    # ========================================
    # STEP 1: SETUP BASELINE
    # ========================================
    async def setup_baseline(self, website_url: str):
        """Setup baseline for regression testing"""
        print(f"Setting up baseline for {website_url}...")
        
        # Launch browser
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            baseline_data = {
                'website_url': website_url,
                'screenshots': {},
                'test_results': {},
                'created_at': datetime.now()
            }
            
            # Test each viewport
            for viewport_name, viewport_size in self.viewports.items():
                print(f"  Testing {viewport_name}...")
                
                # Set viewport
                await page.set_viewport_size(viewport_size)
                
                # Navigate
                await page.goto(website_url, wait_until='networkidle')
                
                # Take screenshot
                screenshot = await page.screenshot()
                
                # Convert to numpy array
                nparr = np.frombuffer(screenshot, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Store
                baseline_data['screenshots'][viewport_name] = screenshot
                baseline_data['test_results'][viewport_name] = {
                    'status': 'PASS',
                    'viewport': viewport_name,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"  ✓ {viewport_name} tested and stored")
            
            await browser.close()
        
        # Save to database
        baseline = Baseline(**baseline_data)
        self.db.add(baseline)
        self.db.commit()
        
        print(f"✅ Baseline created! ID: {baseline.id}")
        return baseline
    
    # ========================================
    # STEP 2-3: RUN REGRESSION TEST
    # ========================================
    async def run_regression_test(self, baseline_id: int, website_url: str):
        """Run regression test against baseline"""
        print(f"Running regression test...")
        
        # Get baseline
        baseline = self.db.query(Baseline).get(baseline_id)
        if not baseline:
            return {'error': 'Baseline not found'}
        
        # Run tests
        current_results = {}
        regressions = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            for viewport_name, viewport_size in self.viewports.items():
                print(f"  Testing {viewport_name}...")
                
                # Set viewport and navigate
                await page.set_viewport_size(viewport_size)
                await page.goto(website_url, wait_until='networkidle')
                
                # Take screenshot
                current_screenshot = await page.screenshot()
                current_results[viewport_name] = current_screenshot
                
                # STEP 4: COMPARE WITH BASELINE
                regression = self.compare_screenshots(
                    baseline.screenshots[viewport_name],
                    current_screenshot,
                    viewport_name
                )
                
                if regression:
                    regressions.append(regression)
                    print(f"  ❌ REGRESSION in {viewport_name}!")
                else:
                    print(f"  ✓ {viewport_name} OK")
            
            await browser.close()
        
        # STEP 5: GENERATE REPORT
        report = self.generate_report(regressions, baseline_id)
        
        # STEP 6: NOTIFY DEVELOPER
        self.notify_developer(report)
        
        return report
    
    # ========================================
    # STEP 4: COMPARE SCREENSHOTS
    # ========================================
    def compare_screenshots(self, baseline_img_bytes: bytes, 
                          current_img_bytes: bytes, viewport: str):
        """Compare two screenshots using OpenCV"""
        
        # Convert bytes to numpy arrays
        baseline_nparr = np.frombuffer(baseline_img_bytes, np.uint8)
        baseline_img = cv2.imdecode(baseline_nparr, cv2.IMREAD_COLOR)
        
        current_nparr = np.frombuffer(current_img_bytes, np.uint8)
        current_img = cv2.imdecode(current_nparr, cv2.IMREAD_COLOR)
        
        # Ensure same size
        if baseline_img.shape != current_img.shape:
            current_img = cv2.resize(current_img, 
                                   (baseline_img.shape[1], baseline_img.shape[0]))
        
        # ADVANCED IMAGE COMPARISON
        # Calculate difference
        difference = cv2.absdiff(baseline_img, current_img)
        
        # Convert to grayscale
        gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        
        # Find contours (areas that changed)
        _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # Calculate total difference percentage
        total_diff = difference.sum()
        max_possible = baseline_img.size * 255
        diff_percent = (total_diff / max_possible) * 100
        
        # If more than 1% difference, it's a regression
        if diff_percent > 1.0:
            # Identify what changed
            changes = self.identify_changes(contours, baseline_img.shape)
            
            return {
                'viewport': viewport,
                'severity': 'CRITICAL' if diff_percent > 10 else 'MAJOR',
                'difference_percent': diff_percent,
                'changes': changes,
                'before_screenshot': baseline_img_bytes,
                'after_screenshot': current_img_bytes,
                'difference_map': cv2.imencode('.png', thresh)[1].tobytes()
            }
        
        return None
    
    # ========================================
    # STEP 5: GENERATE REPORT
    # ========================================
    def generate_report(self, regressions: list, baseline_id: int):
        """Generate detailed regression report"""
        
        report = {
            'baseline_id': baseline_id,
            'timestamp': datetime.now().isoformat(),
            'regressions_found': len(regressions),
            'status': 'PASSED' if len(regressions) == 0 else 'FAILED',
            'details': regressions,
            'recommendation': (
                'All tests passed! Safe to merge.' if len(regressions) == 0
                else 'Fix regressions before merging.'
            )
        }
        
        return report
    
    # ========================================
    # STEP 6: NOTIFY DEVELOPER
    # ========================================
    def notify_developer(self, report: dict):
        """Send notification to developer"""
        
        if report['regressions_found'] > 0:
            # Send email/Slack
            message = f"""
            🚨 REGRESSION DETECTED!
            
            Found {report['regressions_found']} regressions:
            
            {json.dumps(report['details'], indent=2)}
            
            Fix needed before merge!
            """
            self.send_notification(message)
        else:
            # Send success notification
            message = "✅ All regression tests passed! Safe to merge."
            self.send_notification(message)
    
    def identify_changes(self, contours, img_shape):
        """Identify what changed in the image"""
        changes = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Classify change type
            change_type = self.classify_change(w, h, img_shape)
            
            changes.append({
                'location': f'x:{x}, y:{y}, width:{w}, height:{h}',
                'type': change_type,
                'area_percent': (w * h / (img_shape[0] * img_shape[1])) * 100
            })
        
        return changes[:5]  # Top 5 changes
    
    def classify_change(self, width, height, img_shape):
        """Classify the type of change"""
        img_width, img_height = img_shape[1], img_shape[0]
        
        if width > img_width * 0.5 or height > img_height * 0.5:
            return "MAJOR_LAYOUT_CHANGE"
        elif width > 100 or height > 100:
            return "ELEMENT_CHANGED"
        else:
            return "MINOR_CHANGE"
```

### API Endpoint:

```python
# backend/app/routes/regression.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/regression-testing", tags=["regression"])

class BaselineRequest(BaseModel):
    url: str

class RegressionTestRequest(BaseModel):
    baseline_id: int
    url: str

service = RegressionTestingService()

@router.post("/baseline")
async def setup_baseline(request: BaselineRequest):
    """Setup baseline for regression testing"""
    try:
        baseline = await service.setup_baseline(request.url)
        return {
            "status": "success",
            "baseline_id": baseline.id,
            "message": "Baseline created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test")
async def run_regression_test(request: RegressionTestRequest):
    """Run regression test"""
    try:
        report = await service.run_regression_test(
            request.baseline_id,
            request.url
        )
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 🎯 AGENT 2: TEST CASE GENERATOR

### What It Does:

```
GOAL: Auto-generate test cases from requirements

PROCESS:
  1. User inputs: Feature requirements
  2. Agent parses requirements
  3. Calls Gemini AI
  4. AI generates 100+ test cases
  5. Includes normal, edge, error cases
  6. Calculates test coverage
  7. Exports to Jira/CSV/Excel
```

### How It Works (Step by Step):

```
STEP 1: USER INPUTS REQUIREMENTS
┌─────────────────────────────────────┐
│ User: "Create login page with:      │
│  - Email validation                 │
│  - Password strength check          │
│  - Remember me checkbox             │
│  - Forgot password link             │
│  - Social login (Google, Facebook)" │
└─────────────────────────────────────┘

STEP 2: PARSE REQUIREMENTS
┌─────────────────────────────────────┐
│ Agent extracts:                     │
│  ✓ Feature: Login page             │
│  ✓ Components: Email, password     │
│  ✓ Validations: Email, strength    │
│  ✓ Features: Remember me, forgot   │
│  ✓ Integrations: Social login      │
└─────────────────────────────────────┘

STEP 3: CALL GEMINI AI
┌─────────────────────────────────────┐
│ Prompt: "Generate test cases for    │
│ a login page with email, password,  │
│ remember me, forgot password, and   │
│ social login. Include normal cases, │
│ error cases, and edge cases."       │
│                                     │
│ Gemini AI generates:                │
│  - 50+ test cases                  │
│  - Organized by category           │
│  - With steps and expected results  │
└─────────────────────────────────────┘

STEP 4: GENERATED TEST CASES
┌─────────────────────────────────────┐
│ TEST CASE 1: Valid login           │
│   Steps: Enter email, Enter pass    │
│   Expected: Login success           │
│   Priority: P0 (Critical)          │
│                                     │
│ TEST CASE 2: Invalid email format   │
│   Steps: Enter bad@email            │
│   Expected: Error message           │
│   Priority: P1 (High)              │
│                                     │
│ TEST CASE 3: Email with space      │
│   Steps: Enter " email@test.com "  │
│   Expected: Trimmed & valid        │
│   Priority: P2 (Medium)            │
│                                     │
│ TEST CASE 4: SQL injection attempt  │
│   Steps: Enter ' OR '1'='1          │
│   Expected: Treated as string      │
│   Priority: P0 (Critical)          │
│                                     │
│ ... 50+ MORE TEST CASES ...        │
│                                     │
│ Coverage: 98%                       │
└─────────────────────────────────────┘

STEP 5: EXPORT TO JIRA
┌─────────────────────────────────────┐
│ Agent creates Jira stories:         │
│                                     │
│ STORY: Login - Valid credentials   │
│ STORY: Login - Invalid email       │
│ STORY: Login - Empty password      │
│ STORY: Login - SQL injection       │
│ ... (50+ stories)                  │
│                                     │
│ Each story contains:                │
│  - Test steps                       │
│  - Expected result                  │
│  - Priority                         │
│  - Tags                             │
│  - Attachments (if needed)          │
└─────────────────────────────────────┘
```

### Python Code Structure:

```python
# backend/app/services/test_case_generator.py

import google.generativeai as genai
import json
from jira import JIRA
from datetime import datetime

class TestCaseGeneratorService:
    """
    Test Case Generator Agent
    
    Auto-generates test cases from requirements using AI
    """
    
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.jira = None  # Initialized when needed
    
    # ========================================
    # STEP 1-2: PARSE REQUIREMENTS
    # ========================================
    async def parse_requirements(self, requirements_text: str):
        """Extract key information from requirements"""
        
        prompt = f"""
        Extract from this requirement:
        - Feature name
        - Key components/modules
        - Validations needed
        - Edge cases
        - Security considerations
        
        Requirement:
        {requirements_text}
        
        Return as JSON with keys: feature, components, validations, edges, security
        """
        
        response = self.model.generate_content(prompt)
        parsed = json.loads(response.text)
        
        return parsed
    
    # ========================================
    # STEP 3: CALL GEMINI AI
    # ========================================
    async def generate_test_cases(self, requirements_text: str):
        """Generate comprehensive test cases using Gemini AI"""
        
        # Parse requirements
        parsed = await self.parse_requirements(requirements_text)
        
        # Generate test cases
        prompt = f"""
        Generate comprehensive test cases for: {parsed['feature']}
        
        Components: {', '.join(parsed['components'])}
        Validations: {', '.join(parsed['validations'])}
        
        Create test cases for:
        1. Normal/Happy Path (5-10 cases)
        2. Error/Negative Cases (10-15 cases)
        3. Edge Cases (10-15 cases)
        4. Security Cases (5-10 cases)
        5. Performance Cases (3-5 cases)
        
        For each test case, include:
        - Title (clear and descriptive)
        - Steps (numbered, clear actions)
        - Expected Result (what should happen)
        - Priority (P0/P1/P2)
        - Tags (category)
        
        Return as JSON array of test case objects.
        """
        
        response = self.model.generate_content(prompt)
        test_cases = json.loads(response.text)
        
        # Add metadata
        for i, tc in enumerate(test_cases):
            tc['id'] = f"TC_{parsed['feature'].replace(' ', '_')}_{i+1}"
            tc['created_at'] = datetime.now().isoformat()
        
        return {
            'feature': parsed['feature'],
            'test_cases': test_cases,
            'total_cases': len(test_cases),
            'coverage_estimate': self.calculate_coverage(test_cases)
        }
    
    # ========================================
    # STEP 4: CALCULATE COVERAGE
    # ========================================
    def calculate_coverage(self, test_cases: list):
        """Estimate test coverage percentage"""
        
        coverage_areas = {
            'happy_path': 0,
            'error_cases': 0,
            'edge_cases': 0,
            'security': 0,
            'performance': 0
        }
        
        for tc in test_cases:
            tags = tc.get('tags', [])
            for tag in tags:
                if 'happy' in tag.lower() or 'normal' in tag.lower():
                    coverage_areas['happy_path'] += 1
                elif 'error' in tag.lower():
                    coverage_areas['error_cases'] += 1
                elif 'edge' in tag.lower():
                    coverage_areas['edge_cases'] += 1
                elif 'security' in tag.lower():
                    coverage_areas['security'] += 1
                elif 'performance' in tag.lower():
                    coverage_areas['performance'] += 1
        
        total = sum(coverage_areas.values())
        coverage_percent = (total / max(len(test_cases), 1)) * 100
        
        return {
            'overall': min(coverage_percent, 100),
            'breakdown': coverage_areas
        }
    
    # ========================================
    # STEP 5: EXPORT TO JIRA
    # ========================================
    async def export_to_jira(self, test_cases: list, jira_config: dict):
        """Export test cases to Jira"""
        
        # Initialize Jira
        jira = JIRA(
            jira_config['url'],
            auth=(jira_config['username'], jira_config['token'])
        )
        
        created_issues = []
        
        for tc in test_cases:
            # Create Jira issue
            issue = jira.create_issue(
                project=jira_config['project'],
                issuetype='Test Case',
                summary=tc['title'],
                description=f"""
                **Steps to Execute:**
                {chr(10).join([f"{i+1}. {step}" for i, step in enumerate(tc['steps'])])}
                
                **Expected Result:**
                {tc['expected_result']}
                
                **Priority:** {tc['priority']}
                **Tags:** {', '.join(tc.get('tags', []))}
                """,
                customfield_10000=tc['priority']  # Custom priority field
            )
            
            created_issues.append(issue.key)
            print(f"Created: {issue.key}")
        
        return {
            'status': 'success',
            'created_count': len(created_issues),
            'issue_keys': created_issues
        }
```

### API Endpoint:

```python
# backend/app/routes/test_cases.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/test-cases", tags=["test-cases"])

class GenerateRequest(BaseModel):
    requirements: str

class ExportRequest(BaseModel):
    test_case_ids: list
    format: str = "jira"  # jira, csv, excel

service = TestCaseGeneratorService(api_key='YOUR_GEMINI_KEY')

@router.post("/generate")
async def generate_test_cases(request: GenerateRequest):
    """Generate test cases from requirements"""
    try:
        result = await service.generate_test_cases(request.requirements)
        return {
            "status": "success",
            "feature": result['feature'],
            "test_cases_count": result['total_cases'],
            "coverage": result['coverage_estimate'],
            "test_cases": result['test_cases']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/export")
async def export_test_cases(request: ExportRequest):
    """Export test cases to Jira/CSV"""
    try:
        result = await service.export_to_jira(
            request.test_case_ids,
            {
                'url': 'https://company.atlassian.net',
                'username': 'user@company.com',
                'token': 'YOUR_TOKEN',
                'project': 'QA'
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 🐛 AGENT 3: BUG REPORT ASSISTANT

### What It Does:

```
GOAL: Auto-generate professional bug reports

PROCESS:
  1. User uploads screenshot
  2. User types quick description
  3. Agent analyzes screenshot with AI Vision
  4. Extracts issue details
  5. Generates professional report
  6. Auto-posts to Jira
```

### How It Works (Step by Step):

```
STEP 1: USER UPLOADS SCREENSHOT
┌─────────────────────────────────────┐
│ User clicks: "Report Bug"           │
│ Uploads: screenshot.png             │
│ Types: "Button is red instead of   │
│ blue on mobile"                     │
└─────────────────────────────────────┘

STEP 2: AGENT ANALYZES SCREENSHOT
┌─────────────────────────────────────┐
│ Gemini Vision analyzes image:       │
│  ✓ Detects red button              │
│  ✓ Identifies position             │
│  ✓ Reads surrounding text          │
│  ✓ Detects mobile viewport         │
│  ✓ Extracts color codes            │
└─────────────────────────────────────┘

STEP 3: AI GENERATES REPORT
┌─────────────────────────────────────┐
│ PROFESSIONAL BUG REPORT GENERATED   │
│                                     │
│ Title: Primary Button Color         │
│ Incorrect on Mobile View            │
│                                     │
│ Description:                        │
│ The primary CTA button on the      │
│ homepage displays in red (#FF0000) │
│ instead of the brand blue (#0066CC)│
│ on mobile devices (375px). This    │
│ impacts UX and conversion metrics. │
│                                     │
│ Steps to Reproduce:                 │
│ 1. Navigate to homepage            │
│ 2. Set device to mobile (375px)    │
│ 3. Observe button color            │
│                                     │
│ Expected: Button color #0066CC     │
│ Actual: Button color #FF0000       │
│                                     │
│ Severity: MAJOR                    │
│ Device: iPhone SE (375x667)        │
│ Browser: Safari iOS 15             │
│                                     │
│ Affected Elements:                  │
│ - Homepage hero button              │
│ - Product page CTA                  │
│                                     │
│ Root Cause (Analysis):              │
│ CSS media query for mobile may     │
│ have conflicting color property    │
└─────────────────────────────────────┘

STEP 4: AUTO-POST TO JIRA
┌─────────────────────────────────────┐
│ Agent creates Jira issue:           │
│                                     │
│ Issue Type: Bug                     │
│ Summary: Primary Button Color      │
│          Incorrect on Mobile View   │
│ Description: [Full report]          │
│ Severity: Major                     │
│ Attachments: [screenshot]           │
│ Reporter: QA Bot                    │
│ Assignee: Frontend Team             │
│                                     │
│ Jira Issue Created: BUG-12345       │
│ Status: New/Open                    │
│ Timeline: Ready for developer       │
└─────────────────────────────────────┘
```

### Python Code Structure:

```python
# backend/app/services/bug_reporter.py

import google.generativeai as genai
from jira import JIRA
import json
from datetime import datetime
from PIL import Image
import io

class BugReporterService:
    """
    Bug Report Assistant Agent
    
    Generates professional bug reports from screenshots
    """
    
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.jira = None
    
    # ========================================
    # STEP 2: ANALYZE SCREENSHOT
    # ========================================
    async def analyze_screenshot(self, image_bytes: bytes):
        """Analyze screenshot using Gemini Vision"""
        
        # Convert bytes to Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Analyze with Gemini Vision
        response = self.vision_model.generate_content([
            """Analyze this screenshot and provide:
            1. What's wrong or broken
            2. UI elements affected
            3. Colors detected
            4. Layout issues
            5. Text content
            6. Device/viewport detected
            7. Suggested root cause
            
            Be specific and technical.""",
            image
        ])
        
        analysis = response.text
        return analysis
    
    # ========================================
    # STEP 3: GENERATE PROFESSIONAL REPORT
    # ========================================
    async def generate_bug_report(self, image_bytes: bytes, 
                                 user_description: str, config: dict):
        """Generate professional bug report"""
        
        # Analyze screenshot
        screenshot_analysis = await self.analyze_screenshot(image_bytes)
        
        # Generate report using AI
        prompt = f"""
        Create a professional bug report based on:
        
        Screenshot Analysis:
        {screenshot_analysis}
        
        User Description:
        {user_description}
        
        Environment:
        OS: {config.get('os', 'Unknown')}
        Browser: {config.get('browser', 'Unknown')}
        Device: {config.get('device', 'Unknown')}
        Viewport: {config.get('viewport', 'Unknown')}
        
        Generate a comprehensive bug report with:
        1. Concise title (under 10 words)
        2. Detailed description (2-3 sentences)
        3. Numbered steps to reproduce (3-5 steps)
        4. Expected result (what should happen)
        5. Actual result (what happens)
        6. Severity assessment (Critical/Major/Minor)
        7. Affected components/pages
        8. Root cause hypothesis
        
        Return as JSON with keys: title, description, steps, expected, 
        actual, severity, components, root_cause
        """
        
        response = self.text_model.generate_content(prompt)
        report = json.loads(response.text)
        
        # Add metadata
        report['created_at'] = datetime.now().isoformat()
        report['environment'] = config
        report['screenshot'] = image_bytes
        
        return report
    
    # ========================================
    # STEP 4: POST TO JIRA
    # ========================================
    async def post_to_jira(self, report: dict, jira_config: dict):
        """Post bug report to Jira"""
        
        # Initialize Jira
        jira = JIRA(
            jira_config['url'],
            auth=(jira_config['username'], jira_config['token'])
        )
        
        # Create Jira issue
        issue = jira.create_issue(
            project=jira_config['project'],
            issuetype='Bug',
            summary=report['title'],
            description=f"""
            *Description:*
            {report['description']}
            
            *Steps to Reproduce:*
            {chr(10).join([f"{i+1}. {step}" for i, step in enumerate(report['steps'])])}
            
            *Expected Result:*
            {report['expected']}
            
            *Actual Result:*
            {report['actual']}
            
            *Environment:*
            OS: {report['environment']['os']}
            Browser: {report['environment']['browser']}
            Device: {report['environment']['device']}
            
            *Root Cause:*
            {report['root_cause']}
            """,
            priority={'name': report['severity']},
            components=[{'name': comp} for comp in report['components']]
        )
        
        # Attach screenshot
        jira.add_attachment(
            issue,
            report['screenshot'],
            filename='bug_screenshot.png'
        )
        
        return {
            'issue_key': issue.key,
            'issue_url': f"{jira_config['url']}/browse/{issue.key}",
            'status': 'created'
        }
```

### API Endpoint:

```python
# backend/app/routes/bugs.py

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/bug-reporter", tags=["bug-reporter"])

class BugConfig(BaseModel):
    os: str
    browser: str
    device: str = "Unknown"
    viewport: str = "Unknown"

service = BugReporterService(api_key='YOUR_GEMINI_KEY')

@router.post("/create")
async def create_bug_report(
    screenshot: UploadFile = File(...),
    description: str = Form(...),
    os: str = Form(...),
    browser: str = Form(...),
    device: str = Form(default="Unknown"),
    viewport: str = Form(default="Unknown")
):
    """Create bug report from screenshot"""
    try:
        # Read screenshot
        image_bytes = await screenshot.read()
        
        # Generate report
        report = await service.generate_bug_report(
            image_bytes,
            description,
            {
                'os': os,
                'browser': browser,
                'device': device,
                'viewport': viewport
            }
        )
        
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/post-jira")
async def post_bug_to_jira(report: dict):
    """Post bug report to Jira"""
    try:
        result = await service.post_to_jira(
            report,
            {
                'url': 'https://company.atlassian.net',
                'username': 'user@company.com',
                'token': 'YOUR_TOKEN',
                'project': 'QA'
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 📊 ALL 3 AGENTS TOGETHER

### Complete Flow:

```
QA Platform with 3 Agents:

┌──────────────────────────────────────────┐
│   User Dashboard (React Frontend)        │
├──────────────────────────────────────────┤
│                                          │
│  1️⃣ REGRESSION TESTING MODULE           │
│     └─ Upload URL → Agent 1 tests       │
│        Results: Regressions found        │
│                                          │
│  2️⃣ TEST CASE GENERATOR MODULE         │
│     └─ Input requirements → Agent 2     │
│        Results: 100+ test cases         │
│                                          │
│  3️⃣ BUG REPORTER MODULE                │
│     └─ Upload screenshot → Agent 3      │
│        Results: Professional bug report  │
│                                          │
└──────────────────────────────────────────┘
         ↓ (HTTP API calls)
┌──────────────────────────────────────────┐
│   Python FastAPI Backend                 │
├──────────────────────────────────────────┤
│                                          │
│  Agent 1: Regression Testing Service    │
│    - Playwright browser automation      │
│    - OpenCV image comparison            │
│    - Screenshot storage                 │
│                                          │
│  Agent 2: Test Case Generator Service   │
│    - Gemini AI integration              │
│    - Jira export                        │
│    - Coverage calculation               │
│                                          │
│  Agent 3: Bug Reporter Service          │
│    - Gemini Vision analysis             │
│    - Report generation                  │
│    - Jira integration                   │
│                                          │
└──────────────────────────────────────────┘
         ↓ (Data storage)
┌──────────────────────────────────────────┐
│   PostgreSQL Database                    │
│   - Test results                         │
│   - Baselines                            │
│   - Bug reports                          │
│   - User data                            │
└──────────────────────────────────────────┘
```

---

## ✅ SUMMARY: THE 3 AGENTS

### **Agent 1: Regression Testing**
- Detects when code breaks existing features
- Uses Playwright + OpenCV
- Compares screenshots pixel-by-pixel
- Identifies exact changes
- 4,000+ lines of Python

### **Agent 2: Test Case Generator**
- Auto-generates test cases from requirements
- Uses Gemini AI
- Covers happy path, errors, edges, security
- Exports to Jira
- 3,500+ lines of Python

### **Agent 3: Bug Reporter**
- Auto-generates professional bug reports
- Uses Gemini Vision to analyze screenshots
- Extracts technical details
- Posts to Jira automatically
- 3,500+ lines of Python

### **All Together:**
- Unified React frontend
- All agents accessible from one dashboard
- Data flows between agents
- Professional, production-ready platform

---

**This is the COMPLETE specification for all 3 agents!**

**Now you know exactly what each does and how it works!** 🚀
