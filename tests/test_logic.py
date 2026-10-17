import pytest

from utils import repository
from utils.logic import (
    AIAnalysisError, DEPARTMENT_LOOKUP, PRIORITIES, STATUS_OPTIONS, build_options,
    compute_metrics, count_by, department_for_category, display_value, ensure_option,
    filter_issues, filter_options, norm, resolve_department, resolve_technician,
    validate_ai_result,
)

ISSUES = [
    {"id": 1, "title": "AC not working", "description": "Not cooling the room", "location": "Lab 3", "category": "HVAC", "priority": "HIGH", "status": "OPEN", "department": "Facilities", "assigned_to": None},
    {"id": 2, "title": "Wifi down", "description": "No internet", "location": "Library", "category": "IT", "priority": "HIGH", "status": "RESOLVED", "department": "IT", "assigned_to": "Hamza"},
    {"id": 3, "title": None, "description": None, "location": None, "category": None, "priority": "LOW", "status": "OPEN", "department": None, "assigned_to": ""},
    {"id": 4, "title": "Leak", "description": "Tap drips", "location": "Wash", "category": " plumbing ", "priority": "medium", "status": "in progress", "department": "facilities", "assigned_to": "ali"},
    {"id": 5, "title": "Odd", "description": "x", "location": "y", "category": "Spaceship", "priority": "urgent", "status": None, "department": None, "assigned_to": "Zed"},
]


def ids(result):
    return [i["id"] for i in result]


# --- Phase 11: search and filters ------------------------------------------
def test_display_value_handles_null_and_blank():
    assert display_value(None) == "N/A"
    assert display_value("   ", "x") == "x"
    assert display_value("ok") == "ok"


def test_search_covers_title_description_and_location_without_crashing_on_nulls():
    assert ids(filter_issues(ISSUES, "wifi")) == [2]
    assert ids(filter_issues(ISSUES, "NOT COOLING")) == [1]      # description, case-insensitive
    assert ids(filter_issues(ISSUES, "lab")) == [1]              # location
    assert ids(filter_issues(ISSUES, "  drips  ")) == [4]        # surrounding spaces ignored
    assert filter_issues(ISSUES, "zzz") == []


def test_each_filter_individually():
    assert ids(filter_issues(ISSUES, category_filter="HVAC")) == [1]
    assert ids(filter_issues(ISSUES, priority_filter="HIGH")) == [1, 2]
    assert ids(filter_issues(ISSUES, status_filter="OPEN")) == [1, 3]
    assert ids(filter_issues(ISSUES, department_filter="IT")) == [2]
    assert ids(filter_issues(ISSUES, technician_filter="Hamza")) == [2]


def test_filters_are_case_and_whitespace_insensitive_on_stored_data():
    assert ids(filter_issues(ISSUES, category_filter="Plumbing")) == [4]
    assert ids(filter_issues(ISSUES, priority_filter="MEDIUM")) == [4]
    assert ids(filter_issues(ISSUES, status_filter="IN PROGRESS")) == [4]
    assert ids(filter_issues(ISSUES, technician_filter="Ali")) == [4]


def test_missing_values_can_be_filtered():
    assert ids(filter_issues(ISSUES, technician_filter="Unassigned")) == [1, 3]
    assert ids(filter_issues(ISSUES, category_filter="Unknown")) == [3]
    assert ids(filter_issues(ISSUES, status_filter="Unknown")) == [5]
    assert ids(filter_issues(ISSUES, department_filter="Unspecified")) == [3]


def test_filters_combine_with_and_logic():
    assert ids(filter_issues(ISSUES, "wifi", priority_filter="HIGH", status_filter="RESOLVED", department_filter="IT", technician_filter="Hamza")) == [2]
    assert filter_issues(ISSUES, "wifi", priority_filter="HIGH", status_filter="OPEN") == []
    assert ids(filter_issues(ISSUES, priority_filter="HIGH", status_filter="OPEN")) == [1]


def test_all_and_blank_filters_do_not_filter():
    assert len(filter_issues(ISSUES, "", "All", "All", "All", "All", "All")) == len(ISSUES)
    assert len(filter_issues(ISSUES, None, None, "", "all")) == len(ISSUES)


def test_filter_options_come_from_data_and_merge_variants():
    assert filter_options(ISSUES, "priority", PRIORITIES) == ["HIGH", "MEDIUM", "LOW", "URGENT"]
    assert filter_options(ISSUES, "status", STATUS_OPTIONS) == ["OPEN", "IN PROGRESS", "RESOLVED", "Unknown"]
    cats = filter_options(ISSUES, "category")
    assert cats.count("plumbing") == 1 and "Unknown" in cats
    assert build_options(["a", "A ", None, ""], ["B"]) == ["B", "a"]


# --- Phase 12 helpers --------------------------------------------------------
def test_ensure_option_keeps_unlisted_current_value_selectable():
    assert ensure_option(["Ali", "Unassigned"], "ali") == (["Ali", "Unassigned"], 0)
    assert ensure_option(["Ali", "Unassigned"], "Zed") == (["Zed", "Ali", "Unassigned"], 0)
    assert ensure_option(STATUS_OPTIONS, "in progress")[1] == 1
    assert ensure_option(STATUS_OPTIONS, None)[1] == 0


# --- Phase 13: departments -----------------------------------------------------
def test_department_mapping_and_fallbacks():
    assert DEPARTMENT_LOOKUP["hvac"] == "Facilities"
    assert department_for_category(" hvac ") == "Facilities"
    assert department_for_category("Spaceship") == "General Maintenance"
    assert department_for_category(None) == "General Maintenance"


def test_resolve_department_prefers_stored_then_category_then_unspecified():
    assert resolve_department(ISSUES[0]) == "Facilities"
    assert resolve_department(ISSUES[3]) == "Facilities"            # stored 'facilities' -> canonical
    assert resolve_department({"department": None, "category": "IT"}) == "IT"
    assert resolve_department(ISSUES[4]) == "General Maintenance"   # unmapped category
    assert resolve_department(ISSUES[2]) == "Unspecified"
    assert resolve_department({"department": "Custom Team"}) == "Custom Team"


def test_resolve_technician():
    assert [resolve_technician(i) for i in ISSUES] == ["Unassigned", "Hamza", "Unassigned", "Ali", "Zed"]


# --- Phase 14: metrics and counts ----------------------------------------------
def test_metrics_match_records():
    m = compute_metrics(ISSUES)
    assert (m["total"], m["open"], m["in_progress"], m["resolved"], m["unresolved"]) == (5, 2, 1, 1, 4)
    assert (m["high"], m["unassigned"]) == (2, 2)
    assert (m["resolution_rate"], m["high_share"]) == (20, 40)


def test_metrics_on_empty_dataset():
    m = compute_metrics([])
    assert m["total"] == 0 and m["resolution_rate"] == 0 and m["high_share"] == 0


@pytest.mark.parametrize("field", ["category", "priority", "status", "department", "assigned_to"])
def test_chart_counts_always_add_up_to_the_record_count(field):
    assert sum(count_by(ISSUES, field).values()) == len(ISSUES)


def test_count_by_merges_variants_and_orders_known_values_first():
    assert count_by(ISSUES, "priority", PRIORITIES) == {"HIGH": 2, "MEDIUM": 1, "LOW": 1, "URGENT": 1}
    assert list(count_by(ISSUES, "status", STATUS_OPTIONS))[:3] == ["OPEN", "IN PROGRESS", "RESOLVED"]
    assert count_by([], "category") == {}


def test_norm_standardises_inconsistent_values():
    assert norm(" in_progress ") == "IN PROGRESS" and norm(None) == ""


# --- Phase 15: validation of the automated analysis ------------------------------
GOOD = {"category": "hvac", "priority": "high", "ai_summary": " s ", "suggested_action": "a"}


def test_valid_analysis_is_normalised():
    assert validate_ai_result(GOOD) == {"category": "HVAC", "priority": "HIGH", "ai_summary": "s", "suggested_action": "a"}
    assert validate_ai_result([GOOD])["priority"] == "HIGH"
    assert validate_ai_result(dict(GOOD, category="Boilers"))["category"] == "Boilers"


@pytest.mark.parametrize("bad", [
    None, "text", [], [GOOD, GOOD], {},
    dict(GOOD, category=""), dict(GOOD, ai_summary=None), {k: v for k, v in GOOD.items() if k != "priority"},
    dict(GOOD, priority="urgent"), dict(GOOD, priority=3),
])
def test_invalid_analysis_is_rejected(bad):
    with pytest.raises(AIAnalysisError):
        validate_ai_result(bad)


# --- repository -------------------------------------------------------------------
def test_repository_update_requires_a_changed_row():
    from tests import fake_services
    store, _ = fake_services.install()
    assert repository.update_issue(store, 1, {"status": "RESOLVED"})["status"] == "RESOLVED"
    with pytest.raises(repository.IssueUpdateError):
        repository.update_issue(store, 9999, {"status": "RESOLVED"})
    assert repository.fetch_issue(store, 9999) is None
    assert repository.fetch_issue(store, 1)["id"] == 1
    assert len(repository.fetch_issues(store)) == 5
