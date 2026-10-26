"""
Integration tests for Flask application routes, JSON endpoints, error handling, and XSS safety.
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from database.db_manager import init_db
from config import Config


@pytest.fixture
def client():
    """Configures a Flask test client with an isolated temporary SQLite database."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    fd, db_temp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Override database path for test isolation
    original_db_path = Config.DATABASE_PATH
    Config.DATABASE_PATH = Path(db_temp_path)
    init_db(db_path=db_temp_path, reset=True)

    with app.test_client() as test_client:
        yield test_client

    # Cleanup temporary test database
    Config.DATABASE_PATH = original_db_path
    if os.path.exists(db_temp_path):
        try:
            os.remove(db_temp_path)
        except OSError:
            pass


class TestWebRoutes:
    """Tests UI template routes and response codes."""

    def test_homepage_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"TruthLens" in response.data
        assert b"Analyze a News Story" in response.data

    def test_dashboard_loads(self, client):
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"Discourse Analysis Dashboard" in response.data

    def test_history_page_loads(self, client):
        response = client.get("/history")
        assert response.status_code == 200
        assert b"Analysis History" in response.data

    def test_settings_page_loads(self, client):
        response = client.get("/settings")
        assert response.status_code == 200
        assert b"Platform Configuration" in response.data
        assert b"8765" in response.data

    def test_results_dashboard_renders_user_specified_components(self, client):
        from database.db_manager import save_analysis
        import uuid

        analysis_id = str(uuid.uuid4())
        save_analysis({
            "id": analysis_id,
            "title": "LPU Phagwara: A rape rumour sends an Indian university into turmoil",
            "source_type": "url",
            "source_url": "https://www.bbc.com/news/articles/c6kg8dxr54do",
            "publisher": "bbc.com",
            "publish_date": "October 2026",
            "language": "English",
            "summary": "Classes were suspended following unverified rumours on campus.",
            "overall_verdict": "Important claims remain unverified",
            "factual_claims": [
                {
                    "claim": "She also alleged that outsiders had joined the unrest.",
                    "source_passage": "She also alleged that outsiders had joined the unrest.",
                    "verdict": "Not yet verified",
                    "verdict_explanation": "No independent external evidence was located.",
                    "evidence_quality": "Insufficient",
                    "limitations": "No matching open-access reference entries found."
                }
            ],
            "persuasive_techniques": [
                {
                    "technique": "Exaggerated or Dramatic Language",
                    "quote": "turmoil and empties hostels",
                    "explanation": "Highlights heightened public reaction.",
                    "likely_effect": "Presents information in a dramatic reportorial style."
                }
            ],
            "missing_context": "Independent forensic records are required.",
            "status": "completed"
        })

        res = client.get(f"/results/{analysis_id}")
        assert res.status_code == 200
        # Check user's exact dashboard structures
        assert b"Quick Results Dashboard" in res.data
        assert b"Claim Breakdown" in res.data
        assert b"Bias & Style Analysis" in res.data
        assert b"Source & Evidence Profile" in res.data
        assert b"tab-claims" in res.data
        assert b"tab-bias" in res.data
        assert b"tab-source" in res.data
        assert b"btn-claims" in res.data
        assert b"Exact Passage In Article" in res.data
        assert b"Total Factual Claims" in res.data
        assert b"tailwindcss" in res.data
        assert b"lucide" in res.data


    def test_port_in_use_detection(self):
        import socket
        from app import is_port_in_use

        # Create a dummy socket listening on an ephemeral port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            active_port = s.getsockname()[1]

            # Verify function correctly identifies occupied port
            assert is_port_in_use(active_port, "127.0.0.1") is True

        # Now port is closed, should return False
        assert is_port_in_use(active_port, "127.0.0.1") is False


class TestApiEndpoints:
    """Tests JSON endpoints and validation logic."""

    def test_health_check_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["project"] == "TruthLens"
        assert data["port"] == 8765

    def test_api_analyze_empty_input_fails(self, client):
        response = client.post("/api/analyze", json={"content_input": ""})
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Please provide article text" in data["error"]

    def test_api_analyze_ssrf_rejection(self, client):
        response = client.post(
            "/api/analyze",
            json={
                "source_type": "url",
                "content_input": "http://127.0.0.1:8080/admin",
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Security Notice" in data["error"]

    def test_api_analyze_valid_text(self, client):
        payload = {
            "source_type": "text",
            "content_input": (
                "Officials reported that the regional healthcare transition led to a 35% "
                "increase in preventative patient consultations during the first quarter."
            ),
            "custom_title": "Quarterly Health Progress Report",
            "selected_language": "en",
        }
        response = client.post("/api/analyze", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "analysis_id" in data
        assert "redirect_url" in data

        # Check that results page renders saved analysis
        analysis_id = data["analysis_id"]
        res_page = client.get(f"/results/{analysis_id}")
        assert res_page.status_code == 200
        assert b"Quarterly Health Progress Report" in res_page.data

        # Check JSON format export
        json_res = client.get(f"/results/{analysis_id}?format=json")
        assert json_res.status_code == 200
        json_data = json_res.get_json()
        assert json_data["title"] == "Quarterly Health Progress Report"

    def test_api_delete_history(self, client):
        # Create a record first
        payload = {
            "source_type": "text",
            "content_input": "Temporary news story for deletion verification testing.",
            "custom_title": "Delete Me",
        }
        create_res = client.post("/api/analyze", json=payload)
        analysis_id = create_res.get_json()["analysis_id"]

        # Delete it
        del_res = client.delete(f"/api/history/{analysis_id}")
        assert del_res.status_code == 200
        assert del_res.get_json()["success"] is True

        # Ensure subsequent fetch fails
        missing_res = client.get(f"/results/{analysis_id}")
        assert missing_res.status_code == 302  # Redirects to history

    def test_api_test_connection(self, client):
        response = client.post("/api/test-connection")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "mode" in data

    def test_xss_prevention_in_templates(self, client):
        # Attempt script tag injection in headline and body
        xss_title = "<script>alert('xss-title')</script>"
        xss_body = "Legitimate length text with malicious <script>alert('xss-body')</script> embedded."
        payload = {
            "source_type": "text",
            "content_input": xss_body,
            "custom_title": xss_title,
        }
        create_res = client.post("/api/analyze", json=payload)
        analysis_id = create_res.get_json()["analysis_id"]

        # Fetch rendered HTML
        res_page = client.get(f"/results/{analysis_id}")
        html_content = res_page.data.decode("utf-8")

        # Raw executable script tag must NOT be present unescaped
        assert "<script>alert('xss-title')</script>" not in html_content
        # Jinja2 auto-escapes into &lt;script&gt;
        assert "&lt;script&gt;alert(&#39;xss-title&#39;)&lt;/script&gt;" in html_content or "&lt;script&gt;" in html_content
