import os
import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal, engine, Base
from app.models import RequirementSource, TestCaseSuite, TestCase
from app.services.test_case_generator import TestCaseGeneratorService

class TestPhase2TestCaseGenerator(unittest.TestCase):
    def setUp(self):
        # Trigger schema generation
        Base.metadata.create_all(bind=engine)
        self.db: Session = SessionLocal()
        self.client = TestClient(app)
        self.service = TestCaseGeneratorService()

    def tearDown(self):
        self.db.close()
        # Clean up database tables after tests
        Base.metadata.drop_all(bind=engine)

    def test_json_extraction_from_markdown(self):
        """Verify that markdown JSON blocks are successfully extracted and parsed."""
        raw_markdown = """
        Some explanation from the LLM.
        ```json
        {
            "title": "Markdown Suite",
            "test_cases": []
        }
        ```
        Postamble here.
        """
        cleaned = self.service._clean_json_response(raw_markdown)
        self.assertIn('"title": "Markdown Suite"', cleaned)
        self.assertNotIn("```json", cleaned)
        self.assertNotIn("Postamble", cleaned)

    def test_json_extraction_from_plain_text(self):
        """Verify that plain JSON blocks without markdown wrappers are preserved intact."""
        raw_plain = '{"title": "Plain Suite", "test_cases": []}'
        cleaned = self.service._clean_json_response(raw_plain)
        self.assertEqual(cleaned, raw_plain)

    @patch("app.services.llm_adapter.LLMAdapter.generate_text", new_callable=AsyncMock)
    def test_generator_service_database_population(self, mock_generate):
        """Verify that the generator service populates the SQLite tables correctly with LLM data."""
        mock_response = """
        ```json
        {
            "title": "Auth Suite",
            "test_cases": [
                {
                    "test_id": "TC-001",
                    "title": "Verify Login",
                    "description": "Verify user can log in.",
                    "preconditions": "User on landing page",
                    "steps": ["Click Login", "Enter fields"],
                    "expected_result": "Logged in successfully",
                    "priority": "High"
                }
            ]
        }
        ```
        """
        mock_generate.return_value = mock_response

        # Execute direct service logic using asyncio.run()
        import asyncio
        result = asyncio.run(self.service.generate_suite_from_requirements(
            requirements_content="Simple login requirement details.",
            title="Custom Request Title",
            provider="gemini",
            model="gemini-1.5-flash",
            api_key="mock-key-123",
            db=self.db
        ))

        # Assert returned payload
        self.assertEqual(result["title"], "Auth Suite")
        self.assertEqual(len(result["test_cases"]), 1)
        self.assertEqual(result["test_cases"][0]["test_id"], "TC-001")

        # Query Database directly and check state
        suite_in_db = self.db.query(TestCaseSuite).filter(TestCaseSuite.id == result["suite_id"]).first()
        self.assertIsNotNone(suite_in_db)
        self.assertEqual(suite_in_db.title, "Auth Suite")
        self.assertEqual(len(suite_in_db.test_cases), 1)

        req_in_db = self.db.query(RequirementSource).filter(RequirementSource.id == result["requirement_id"]).first()
        self.assertIsNotNone(req_in_db)
        self.assertEqual(req_in_db.content, "Simple login requirement details.")

    def test_generate_endpoint_requires_api_key(self):
        """Verify that calling the generate endpoint without a transistent API Key throws 400 Bad Request."""
        payload = {
            "requirements": "Verify search bar works.",
            "title": "Search Bar Verification"
        }
        response = self.client.post(
            "/api/test-cases/generate",
            json=payload,
            headers={"X-LLM-Provider": "openai", "X-LLM-Model": "gpt-4o-mini"} # No X-LLM-API-Key header
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("API Key is missing", response.json()["detail"])

    @patch("app.services.llm_adapter.LLMAdapter.generate_text", new_callable=AsyncMock)
    def test_generate_endpoint_success_and_db_flow(self, mock_generate):
        """Verify the full HTTP post generate, list, and delete workflow."""
        # Setup mock behavior
        mock_generate.return_value = """
        {
            "title": "Mock API Suite",
            "test_cases": [
                {
                    "test_id": "TC-101",
                    "title": "API Verification",
                    "description": "Check endpoints",
                    "preconditions": "Server active",
                    "steps": ["Call endpoint"],
                    "expected_result": "Returns 200",
                    "priority": "Medium"
                }
            ]
        }
        """

        # 1. Trigger Generation
        payload = {"requirements": "Test API constraints.", "title": "API Verification Suite"}
        headers = {
            "X-LLM-Provider": "gemini",
            "X-LLM-Model": "gemini-1.5-flash",
            "X-LLM-API-Key": "transient-gemini-key-123"
        }
        response = self.client.post("/api/test-cases/generate", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        suite_id = response.json()["suite_id"]

        # 2. List Suites
        list_response = self.client.get("/api/test-cases/suites")
        self.assertEqual(list_response.status_code, 200)
        suites = list_response.json()
        self.assertTrue(any(s["id"] == suite_id for s in suites))
        self.assertEqual(suites[0]["test_case_count"], 1)

        # 3. Retrieve Single Suite Details
        detail_response = self.client.get(f"/api/test-cases/suites/{suite_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail_data = detail_response.json()
        self.assertEqual(detail_data["title"], "Mock API Suite")
        self.assertEqual(len(detail_data["test_cases"]), 1)
        self.assertEqual(detail_data["test_cases"][0]["test_id"], "TC-101")

        # 4. Delete Suite and check Cascade
        delete_response = self.client.delete(f"/api/test-cases/suites/{suite_id}")
        self.assertEqual(delete_response.status_code, 200)

        # Ensure deleted from DB
        get_response = self.client.get(f"/api/test-cases/suites/{suite_id}")
        self.assertEqual(get_response.status_code, 404)

        # Direct database checks for cascading
        test_cases_left = self.db.query(TestCase).filter(TestCase.suite_id == suite_id).all()
        self.assertEqual(len(test_cases_left), 0)

if __name__ == "__main__":
    unittest.main()
