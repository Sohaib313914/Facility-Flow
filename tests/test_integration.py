"""Optional integration tests against the REAL Supabase project and Gemini API.

They are skipped automatically unless SUPABASE_URL, SUPABASE_KEY and GEMINI_API_KEY are
available (from the environment or your .env). They only READ from Supabase and make one
small Gemini request; they never insert, update or delete data.

Run:  python -m pytest tests/test_integration.py -v
"""
import os
import sys

import pytest
from dotenv import load_dotenv

load_dotenv()
REQUIRED = ("SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY")
MISSING = [name for name in REQUIRED if not os.getenv(name)]

pytestmark = pytest.mark.skipif(
    bool(MISSING), reason="missing credentials: " + ", ".join(MISSING)
)

EXPECTED_COLUMNS = {
    "id", "title", "description", "location", "category", "priority", "department",
    "status", "assigned_to", "ai_summary", "suggested_action", "created_at",
}


@pytest.fixture(scope="module")
def real_services():
    # Other test modules install in-memory fakes; make sure the real modules are imported.
    for name in ("services", "services.database", "services.ai_service"):
        sys.modules.pop(name, None)
    from services import ai_service, database
    return database.supabase, ai_service


def test_supabase_issues_table_is_readable_and_has_the_expected_columns(real_services):
    from utils import repository
    client, _ = real_services
    issues = repository.fetch_issues(client)
    assert isinstance(issues, list)
    if issues:
        assert EXPECTED_COLUMNS <= set(issues[0].keys())


def test_filters_and_metrics_work_on_real_records(real_services):
    from utils import repository
    from utils.logic import compute_metrics, count_by, filter_issues
    client, _ = real_services
    issues = repository.fetch_issues(client)
    assert len(filter_issues(issues)) == len(issues)
    assert sum(count_by(issues, "status").values()) == len(issues)
    assert compute_metrics(issues)["total"] == len(issues)


def test_gemini_returns_a_valid_analysis(real_services):
    from utils.logic import validate_ai_result
    _, ai = real_services
    assert ai.MODEL == "gemini-3.5-flash-lite"
    result = validate_ai_result(
        ai.analyze_issue("Air conditioner not cooling", "The AC in lab 3 blows warm air since morning.")
    )
    assert result["priority"] in ("LOW", "MEDIUM", "HIGH")
