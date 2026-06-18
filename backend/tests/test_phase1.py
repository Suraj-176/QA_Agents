import os
import unittest
from fastapi.testclient import TestClient

class TestPhase1Core(unittest.TestCase):
    def setUp(self):
        # Import inside setUp so database setup is triggered
        from app.main import app
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Verify the health-check root endpoint works and lists supported agents."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("supported_agents", data)
        self.assertEqual(len(data["supported_agents"]), 3)

    def test_database_creation(self):
        """Verify that SQLite database and static assets directory are successfully created on initialization."""
        db_path = "./qa_platform.db"
        # The DB table generation is run on startup, so the file must exist
        self.assertTrue(os.path.exists(db_path), f"SQLite database file not found at {db_path}")

        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
        self.assertTrue(os.path.exists(static_dir), f"Static directory not found at {static_dir}")

if __name__ == "__main__":
    unittest.main()
