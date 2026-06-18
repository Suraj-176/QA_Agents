import os
import shutil
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from io import BytesIO
from PIL import Image

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models import BugReport
from app.services.bug_reporter import BugReporterService

class TestPhase4BugReporter(unittest.TestCase):
    def setUp(self):
        # Trigger database schema setup
        Base.metadata.create_all(bind=engine)
        self.db: Session = SessionLocal()
        self.client = TestClient(app)
        self.service = BugReporterService()

        # Temporary folder setup
        self.bugs_folder = os.path.join(self.service.static_dir, "bugs")
        os.makedirs(self.bugs_folder, exist_ok=True)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)
        
        # Purge files inside static/bugs
        shutil.rmtree(self.bugs_folder, ignore_errors=True)

    def _generate_dummy_image_bytes(self) -> bytes:
        """Helper to create raw bytes of a visual PNG screenshot."""
        img = Image.new("RGB", (100, 100), color="yellow")
        out = BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()

    @patch("app.services.llm_adapter.LLMAdapter.analyze_image", new_callable=AsyncMock)
    def test_analyze_screenshot_success_and_db_persistence(self, mock_vision):
        """Verify that uploaded images are audited by LLM Vision and persisted locally."""
        # 1. Setup mock vision response
        mock_vision.return_value = """
        ```json
        {
            "title": "[Admin Dashboard] Broken charts overlapping sidebar",
            "description": "The visual charts in the home module are clipping and overlapping into the sidebar navigation.",
            "steps_to_reproduce": [
                "Step 1: Click Admin Dashboard tab",
                "Step 2: Scroll to graph module"
            ],
            "expected_result": "Charts resize dynamically to accommodate the viewport grid.",
            "severity": "High"
        }
        ```
        """

        # 2. Fire Multipart upload via Client
        img_bytes = self._generate_dummy_image_bytes()
        files = {
            "file": ("screenshot_broken_layout.png", img_bytes, "image/png")
        }
        data = {
            "description": "The graph elements are messed up!"
        }
        headers = {
            "X-LLM-Provider": "gemini",
            "X-LLM-Model": "gemini-1.5-flash",
            "X-LLM-API-Key": "transient-key-mock-123"
        }

        response = self.client.post("/api/bug-reporter/analyze", files=files, data=data, headers=headers)
        self.assertEqual(response.status_code, 201)
        
        res_data = response.json()
        bug_id = res_data["bug_id"]
        self.assertEqual(res_data["severity"], "High")
        self.assertEqual(res_data["status"], "draft")

        # 3. Check file is saved to disk
        local_path = os.path.join(self.service.static_dir, res_data["screenshot_path"])
        self.assertTrue(os.path.exists(local_path), f"File was not saved to {local_path}")

        # 4. Check DB state
        bug_db = self.db.query(BugReport).filter(BugReport.id == bug_id).first()
        self.assertIsNotNone(bug_db)
        self.assertIn("Visual Bug Details", bug_db.description)
        self.assertIn("overlapping sidebar", bug_db.title)

    @patch("requests.post")
    def test_jira_export_success_and_state_transition(self, mock_post):
        """Verify that bug reports are successfully mapped and pushed as Atlassian JIRA issues with attachments."""
        # 1. Inject a draft bug report in SQLite
        img_bytes = self._generate_dummy_image_bytes()
        filename = "temp_snap.png"
        
        # Save dummy screenshot file locally
        filepath = os.path.join(self.bugs_folder, f"123_{filename}")
        with open(filepath, "wb") as f:
            f.write(img_bytes)

        bug = BugReport(
            title="Broken Cart Layout",
            description="The checkout checkout button wraps offscreen.",
            severity="Critical",
            screenshot_path="bugs/123_temp_snap.png",
            status="draft"
        )
        self.db.add(bug)
        self.db.commit()

        # 2. Setup mock response for JIRA API
        # Mock issue creation response (201 Created)
        mock_res_create = MagicMock()
        mock_res_create.status_code = 201
        mock_res_create.json.return_value = {
            "id": "10001",
            "key": "QA-101",
            "self": "https://test-jira.atlassian.net/rest/api/3/issue/10001"
        }

        # Mock attachment response (200 OK)
        mock_res_attach = MagicMock()
        mock_res_attach.status_code = 200

        # Configure mock post to return creation first, then attachment
        mock_post.side_effect = [mock_res_create, mock_res_attach]

        # 3. Execute Export Endpoint
        export_payload = {
            "jira_domain": "test-jira",
            "jira_email": "qa@company.com",
            "jira_token": "token123",
            "jira_project": "QA"
        }

        response = self.client.post(f"/api/bug-reporter/export/{bug.id}", json=export_payload)
        self.assertEqual(response.status_code, 200)

        # 4. Check JIRA mappings
        res_data = response.json()
        self.assertEqual(res_data["jira_key"], "QA-101")
        self.assertEqual(res_data["status"], "submitted_to_jira")
        self.assertEqual(res_data["jira_url"], "https://test-jira.atlassian.net/browse/QA-101")

        # Check DB updated state after refreshing session cache
        self.db.expire_all()
        updated_bug = self.db.query(BugReport).filter(BugReport.id == bug.id).first()
        self.assertEqual(updated_bug.status, "submitted_to_jira")
        self.assertEqual(updated_bug.jira_key, "QA-101")

    def test_list_and_delete_cleanup_cascade(self):
        """Verify listing works and that deleting a bug report removes both SQL records and local disk files."""
        # 1. Add dummy record and write dummy file on disk
        filename = "cleanup_snap.png"
        filepath = os.path.join(self.bugs_folder, filename)
        with open(filepath, "wb") as f:
            f.write(b"mock_bytes")

        bug = BugReport(
            title="Temp Bug for deletion",
            description="Details",
            severity="Low",
            screenshot_path=f"bugs/{filename}",
            status="draft"
        )
        self.db.add(bug)
        self.db.commit()

        # 2. Check listing has it
        list_res = self.client.get("/api/bug-reporter/reports")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 1)

        # 3. Delete report
        delete_res = self.client.delete(f"/api/bug-reporter/reports/{bug.id}")
        self.assertEqual(delete_res.status_code, 200)

        # 4. Check DB row is gone
        db_check = self.db.query(BugReport).filter(BugReport.id == bug.id).first()
        self.assertIsNone(db_check)

        # 5. Check local file was removed from disk automatically
        self.assertFalse(os.path.exists(filepath), f"File {filepath} was not removed from disk.")

if __name__ == "__main__":
    unittest.main()
