import os
import shutil
import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from PIL import Image

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models import Baseline, RegressionTestRun, RegressionTestResult
from app.services.regression_testing import RegressionTestingService

class TestPhase3RegressionTesting(unittest.TestCase):
    def setUp(self):
        # Trigger database schema setup
        Base.metadata.create_all(bind=engine)
        self.db: Session = SessionLocal()
        self.client = TestClient(app)
        self.service = RegressionTestingService()

        # Create temporary folders for testing assets
        self.temp_dir = os.path.join(self.service.static_dir, "temp_test_assets")
        os.makedirs(self.temp_dir, exist_ok=True)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)
        
        # Clean up created files and folders
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clean static subfolders
        static_baselines = os.path.join(self.service.static_dir, "baselines")
        static_runs = os.path.join(self.service.static_dir, "runs")
        shutil.rmtree(static_baselines, ignore_errors=True)
        shutil.rmtree(static_runs, ignore_errors=True)

    def _generate_test_image(self, color, square_color=None) -> str:
        """Helper to create a solid color image with an optional visual square shape."""
        img = Image.new("RGB", (200, 200), color=color)
        if square_color:
            # Draw a shape
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 150, 150], fill=square_color)
        
        # Save to temp directory
        filename = f"img_{color}_{square_color or 'solid'}.png"
        path = os.path.join(self.temp_dir, filename)
        img.save(path)
        return path

    def test_opencv_comparison_identical(self):
        """Verify that comparing identical images yields 100% similarity and no mismatch flag."""
        img1 = self._generate_test_image("white", "blue")
        img2 = self._generate_test_image("white", "blue")
        diff_path = os.path.join(self.temp_dir, "diff_identical.png")

        similarity, is_mismatch = self.service._compare_images(img1, img2, diff_path)

        self.assertEqual(similarity, 100.0)
        self.assertFalse(is_mismatch)
        self.assertTrue(os.path.exists(diff_path))

    def test_opencv_comparison_mismatch(self):
        """Verify that comparing layout-shifted images yields sub-100% similarity and triggers mismatch flag."""
        img1 = self._generate_test_image("white", "blue")
        img2 = self._generate_test_image("white", "red") # Color mismatch!
        diff_path = os.path.join(self.temp_dir, "diff_mismatch.png")

        similarity, is_mismatch = self.service._compare_images(img1, img2, diff_path)

        self.assertLess(similarity, 100.0)
        self.assertTrue(is_mismatch)
        self.assertTrue(os.path.exists(diff_path))

    @patch("app.services.regression_testing.RegressionTestingService._capture_screenshots")
    def test_setup_baseline_creates_db_entries(self, mock_capture):
        """Verify that setting up a baseline triggers captures and creates the required database logs."""
        # Setup mock file structure to match capture output
        mock_baseline_folder = os.path.join(self.service.static_dir, "baselines", "1")
        os.makedirs(mock_baseline_folder, exist_ok=True)
        
        # Write dummy files to simulate screenshots taken by Playwright
        captured_mocks = {}
        for vp in ["desktop", "tablet", "mobile"]:
            path = os.path.join(mock_baseline_folder, f"{vp}.png")
            Image.new("RGB", (100, 100), color="white").save(path)
            captured_mocks[vp] = path

        # Set mock return value
        mock_capture.return_value = captured_mocks

        # Trigger Service Method
        import asyncio
        result = asyncio.run(self.service.setup_baseline(
            name="Landing Page",
            url="http://example.com",
            db=self.db
        ))

        # Check returned details
        self.assertEqual(result["name"], "Landing Page")
        self.assertEqual(result["screenshots_count"], 3)

        # Check Database state
        baseline_db = self.db.query(Baseline).filter(Baseline.id == result["baseline_id"]).first()
        self.assertIsNotNone(baseline_db)
        self.assertEqual(len(baseline_db.screenshots), 3)
        self.assertEqual(baseline_db.screenshots[0].viewport, "desktop")

    @patch("app.services.regression_testing.RegressionTestingService._capture_screenshots")
    def test_full_regression_run_flow(self, mock_capture):
        """Verify the complete HTTP trigger, background task run, and diff analysis flow."""
        # 1. Create a dummy baseline in DB with dummy baseline images on disk
        baseline = Baseline(name="Mock App", url="http://base.com")
        self.db.add(baseline)
        self.db.flush()

        base_folder = os.path.join(self.service.static_dir, "baselines", str(baseline.id))
        os.makedirs(base_folder, exist_ok=True)

        for vp in ["desktop", "tablet", "mobile"]:
            img_path = os.path.join(base_folder, f"{vp}.png")
            # Create a solid blue image for baseline (guarantees huge grayscale difference from red)
            Image.new("RGB", (100, 100), color="blue").save(img_path)
            
            from app.models import BaselineScreenshot
            scr = BaselineScreenshot(
                baseline_id=baseline.id,
                viewport=vp,
                image_path=os.path.relpath(img_path, self.service.static_dir).replace("\\", "/")
            )
            self.db.add(scr)
        self.db.commit()

        # 2. Mock target run screenshot captures (solid red to guarantee a mismatch / regression!)
        run_folder = os.path.join(self.service.static_dir, "runs", "1") # Expect run ID 1
        os.makedirs(run_folder, exist_ok=True)
        
        captured_run_mocks = {}
        for vp in ["desktop", "tablet", "mobile"]:
            path = os.path.join(run_folder, f"{vp}.png")
            Image.new("RGB", (100, 100), color="red").save(path)
            captured_run_mocks[vp] = path

        mock_capture.return_value = captured_run_mocks

        # 3. Request visual test via HTTP Client
        payload = {
            "baseline_id": baseline.id,
            "target_url": "http://target-run.com"
        }
        response = self.client.post("/api/regression-testing/test", json=payload)
        self.assertEqual(response.status_code, 202)
        run_id = response.json()["run_id"]

        # Since BackgroundTasks run in sync mode inside TestClient, the task has already run on the same thread!
        # 4. Fetch test run details and verify visual regressions
        run_detail_response = self.client.get(f"/api/regression-testing/runs/{run_id}")
        self.assertEqual(run_detail_response.status_code, 200)

        run_data = run_detail_response.json()
        self.assertEqual(run_data["status"], "completed")
        self.assertIn("Visual Regressions Detected", run_data["summary"])
        self.assertEqual(len(run_data["results"]), 3)
        
        # Verify specific mismatch results
        for res in run_data["results"]:
            self.assertTrue(res["is_mismatch"])
            self.assertLess(res["similarity_score"], 10.0) # Green vs Red is highly dissimilar
            self.assertTrue(os.path.exists(os.path.join(self.service.static_dir, res["diff_image_path"])))

if __name__ == "__main__":
    unittest.main()
