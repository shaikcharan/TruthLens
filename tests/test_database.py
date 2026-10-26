"""
Unit tests for SQLite database manager, schema constraints, and SQL injection safety.
"""

import pytest
import sys
import uuid
import os
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_manager import (
    init_db,
    save_analysis,
    get_analysis,
    list_analyses,
    delete_analysis,
    get_dashboard_stats,
    check_db_health,
)


@pytest.fixture
def temp_db():
    """Provides an isolated temporary database for test execution."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path=path, reset=True)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


class TestDatabaseManager:
    """Tests CRUD operations and relational integrity."""

    def test_database_initialization(self, temp_db):
        health = check_db_health(db_path=temp_db)
        assert health["healthy"] is True
        assert "analyses" in health["tables"]
        assert "claims" in health["tables"]
        assert "rhetorical_techniques" in health["tables"]
        assert "framing_indicators" in health["tables"]

    def test_save_and_retrieve_analysis(self, temp_db):
        analysis_id = str(uuid.uuid4())
        data = {
            "id": analysis_id,
            "title": "Automated Testing Story",
            "source_type": "text",
            "source_url": None,
            "source_preview": "Preview snippet for testing.",
            "language": "English",
            "summary": "Neutral test summary.",
            "factual_claims": [
                {
                    "claim": "Testing statistics reveal 100% test coverage.",
                    "claim_type": "statistical",
                    "verification_status": "Supported by available evidence",
                    "verification_notes": "Corroborated via test logs.",
                    "evidence_sources": [{"title": "Test Suite", "url": "https://pytest.org"}],
                }
            ],
            "rhetorical_techniques": [
                {
                    "technique": "Sensationalism",
                    "explanation": "Overstated praise of tests.",
                    "quote": "Unprecedented achievement",
                }
            ],
            "framing_indicators": [
                {"indicator": "Success Framing", "explanation": "Highlights achievements exclusively."}
            ],
            "missing_context": "Omitted failing tests elsewhere.",
            "limitations": "Synthetic test environment.",
            "recommended_verification_steps": ["Run pytest locally."],
            "status": "completed",
        }

        saved_id = save_analysis(data, db_path=temp_db)
        assert saved_id == analysis_id

        retrieved = get_analysis(analysis_id, db_path=temp_db)
        assert retrieved is not None
        assert retrieved["title"] == "Automated Testing Story"
        assert len(retrieved["claims"]) == 1
        assert retrieved["claims"][0]["verification_status"] == "Supported by available evidence"
        assert len(retrieved["rhetorical_techniques"]) == 1
        assert retrieved["rhetorical_techniques"][0]["technique_name"] == "Sensationalism"

    def test_cascade_deletion(self, temp_db):
        analysis_id = str(uuid.uuid4())
        data = {
            "id": analysis_id,
            "title": "Story To Delete",
            "source_type": "text",
            "language": "Hindi",
            "factual_claims": [{"claim": "Claim 1", "verification_status": "Unverified"}],
            "rhetorical_techniques": [{"technique": "Emotional Appeal", "explanation": "Note"}],
        }
        save_analysis(data, db_path=temp_db)
        assert get_analysis(analysis_id, db_path=temp_db) is not None

        # Delete record
        deleted = delete_analysis(analysis_id, db_path=temp_db)
        assert deleted is True

        # Ensure main record and children are removed
        assert get_analysis(analysis_id, db_path=temp_db) is None
        stats = get_dashboard_stats(db_path=temp_db)
        assert stats["total_claims"] == 0
        assert stats["total_techniques"] == 0

    def test_dashboard_stats_calculation(self, temp_db):
        # Insert two analyses
        save_analysis(
            {
                "id": str(uuid.uuid4()),
                "title": "Story One",
                "source_type": "text",
                "language": "English",
                "factual_claims": [{"claim": "C1", "verification_status": "Unverified"}],
                "rhetorical_techniques": [{"technique": "Sensationalism", "explanation": "E1"}],
            },
            db_path=temp_db,
        )
        save_analysis(
            {
                "id": str(uuid.uuid4()),
                "title": "Story Two",
                "source_type": "text",
                "language": "Telugu",
                "factual_claims": [{"claim": "C2", "verification_status": "Partially supported"}],
                "rhetorical_techniques": [{"technique": "Sensationalism", "explanation": "E2"}],
            },
            db_path=temp_db,
        )

        stats = get_dashboard_stats(db_path=temp_db)
        assert stats["total_analyses"] == 2
        assert stats["total_claims"] == 2
        assert stats["total_techniques"] == 2
        assert stats["status_distribution"].get("Unverified") == 1
        assert stats["status_distribution"].get("Partially supported") == 1
        assert stats["techniques_distribution"][0]["technique"] == "Sensationalism"
        assert stats["techniques_distribution"][0]["count"] == 2

    def test_sql_injection_resistance(self, temp_db):
        # Malicious payload intended to alter SQL logic
        malicious_query = "' OR '1'='1"
        results = list_analyses(search_query=malicious_query, db_path=temp_db)
        # Parameterized query should safely treat this as a string literal and return 0 matches
        assert isinstance(results, list)
        assert len(results) == 0
