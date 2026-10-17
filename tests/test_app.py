"""End-to-end UI tests using Streamlit's AppTest with fake Supabase/Gemini (no credentials)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests import fake_services

APP = str(Path(__file__).resolve().parent.parent / "app.py")
DASH, ISSUES, REPORT, ANALYTICS = "📊  Dashboard", "📋  Issues", "➕  Report Issue", "📈  Analytics"


@pytest.fixture
def app():
    store, ai = fake_services.install()
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    at.store, at.ai = store, ai
    return at


NAV_SLUGS = {DASH: "dashboard", ISSUES: "issues", REPORT: "report", ANALYTICS: "analytics"}


def open_page(at, page):
    """Click the sidebar navigation button, like a user would."""
    at.button(key=f"navbtn_{NAV_SLUGS[page]}").click().run()


def go(at, page):
    open_page(at, page)
    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]


def issue_select(at):
    return [s for s in at.selectbox if s.label == "Select an issue"][0]


def test_every_page_renders(app):
    for page in (ISSUES, REPORT, ANALYTICS, DASH):
        go(app, page)


def test_branding(app):
    html = " ".join(m.value for m in app.markdown)
    assert "FacilityFlow" in html and "MaintainIQ" not in html


def test_every_issue_detail_renders_including_null_fields(app):
    go(app, ISSUES)
    for opt in list(issue_select(app).options):
        issue_select(app).set_value(opt).run()
        assert not app.exception, opt


def test_user_text_is_escaped(app):
    go(app, ISSUES)
    issue_select(app).set_value("2 - Flickering <b>lights</b>").run()
    html = " ".join(m.value for m in app.markdown)
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_filters_and_search(app):
    go(app, ISSUES)
    [s for s in app.selectbox if "Priority" in s.label][0].set_value("HIGH").run()
    assert len(issue_select(app).options) == 2
    [s for s in app.selectbox if "Priority" in s.label][0].set_value("All").run()
    [t for t in app.text_input if "Search" in t.label][0].set_value("wifi").run()
    assert issue_select(app).options == ["5 - Wifi down"]


def test_assign_and_update_status_persist(app):
    go(app, ISSUES)
    app.selectbox(key="technician_1").set_value("Hamza").run()
    [b for b in app.button if b.key == "assign_btn_1"][0].click().run()
    app.selectbox(key="status_1").set_value("RESOLVED").run()
    [b for b in app.button if b.key == "status_btn_1"][0].click().run()
    row = [r for r in app.store.rows if r["id"] == 1][0]
    assert (row["assigned_to"], row["status"]) == ("Hamza", "RESOLVED")
    app.selectbox(key="technician_1").set_value("Unassigned").run()
    [b for b in app.button if b.key == "assign_btn_1"][0].click().run()
    assert [r for r in app.store.rows if r["id"] == 1][0]["assigned_to"] is None


def test_report_issue_validation_and_insert(app):
    go(app, REPORT)
    before = len(app.store.rows)
    [b for b in app.button if b.label == "Submit Issue"][0].click().run()
    assert app.warning and len(app.store.rows) == before
    [t for t in app.text_input if t.label == "Issue Title"][0].set_value("Water heater cold")
    app.text_area[0].set_value("No hot water")
    [t for t in app.text_input if t.label == "Location"][0].set_value("Hostel A")
    [b for b in app.button if b.label == "Submit Issue"][0].click().run()
    assert not app.exception and not app.error
    assert len(app.store.rows) == before + 1
    new = app.store.rows[0]
    assert (new["status"], new["department"]) == ("OPEN", "Facilities")
    assert [t for t in app.text_input if t.label == "Issue Title"][0].value == ""  # form reset


def test_gemini_failure_is_reported_not_crashing(app):
    def boom(title, description):
        raise RuntimeError("quota exceeded")
    app.ai.analyze_issue = boom
    go(app, REPORT)
    [t for t in app.text_input if t.label == "Issue Title"][0].set_value("x")
    app.text_area[0].set_value("y")
    [t for t in app.text_input if t.label == "Location"][0].set_value("z")
    before = len(app.store.rows)
    [b for b in app.button if b.label == "Submit Issue"][0].click().run()
    assert not app.exception
    assert any("quota exceeded" in e.value for e in app.error)
    assert len(app.store.rows) == before


def test_missing_credentials_shows_friendly_message():
    import sys
    for name in ("services", "services.database", "services.ai_service"):
        sys.modules.pop(name, None)
    sys.modules["services"] = None  # makes `from services...` raise ImportError
    try:
        at = AppTest.from_file(APP, default_timeout=30).run()
        assert not at.exception
        assert any("could not start" in e.value for e in at.error)
    finally:
        sys.modules.pop("services", None)


# ---------------------------------------------------------------------------
# Phases 11-15: additional UI behaviour
# ---------------------------------------------------------------------------
def select(at, label_part):
    return [s for s in at.selectbox if label_part in s.label][0]


def fill_and_submit(at, title="Water heater cold", desc="No hot water", loc="Hostel A"):
    [t for t in at.text_input if t.label == "Issue Title"][0].set_value(title)
    at.text_area[0].set_value(desc)
    [t for t in at.text_input if t.label == "Location"][0].set_value(loc)
    [b for b in at.button if b.label == "Submit Issue"][0].click().run()


def test_department_and_technician_filters_and_description_search(app):
    go(app, ISSUES)
    select(app, "Department").set_value("IT").run()
    assert issue_select(app).options == ["5 - Wifi down"]
    select(app, "Department").set_value("All").run()
    select(app, "Technician").set_value("Unassigned").run()
    assert issue_select(app).options == ["1 - AC not working"]
    select(app, "Technician").set_value("All").run()
    [t for t in app.text_input if "Search" in t.label][0].set_value("internet").run()  # description text
    assert issue_select(app).options == ["5 - Wifi down"]


def test_combined_filters_and_empty_result_message(app):
    go(app, ISSUES)
    select(app, "Priority").set_value("HIGH").run()
    select(app, "Status").set_value("RESOLVED").run()
    assert not app.selectbox or all(s.label != "Select an issue" for s in app.selectbox)
    assert any("No issues match" in i.value for i in app.info)
    assert not app.exception


def test_clear_filters_button_resets_everything(app):
    go(app, ISSUES)
    select(app, "Priority").set_value("HIGH").run()
    [t for t in app.text_input if "Search" in t.label][0].set_value("wifi").run()
    [b for b in app.button if b.label == "Clear filters"][0].click().run()
    assert select(app, "Priority").value == "All"
    assert [t for t in app.text_input if "Search" in t.label][0].value == ""
    assert len(issue_select(app).options) == 5


def test_technician_not_in_standard_list_is_preserved(app):
    go(app, ISSUES)
    issue_select(app).set_value("4 - Projector dead").run()
    tech = app.selectbox(key="technician_4")
    assert tech.value == "Zed"                       # shown as stored, not silently 'Unassigned'
    app.selectbox(key="status_4").set_value("IN PROGRESS").run()
    [b for b in app.button if b.key == "status_btn_4"][0].click().run()
    row = [r for r in app.store.rows if r["id"] == 4][0]
    assert row["status"] == "IN PROGRESS" and row["assigned_to"] == "Zed"


def test_update_failure_is_shown_and_nothing_changes(app):
    go(app, ISSUES)
    app.store.fail["update"] = RuntimeError("db down")
    app.selectbox(key="status_1").set_value("RESOLVED").run()
    [b for b in app.button if b.key == "status_btn_1"][0].click().run()
    assert not app.exception
    assert any("Failed to update status" in e.value and "db down" in e.value for e in app.error)
    assert not app.success
    assert [r for r in app.store.rows if r["id"] == 1][0]["status"] == "OPEN"


def test_issue_that_disappears_between_list_and_detail_shows_a_warning(app, monkeypatch):
    from utils import repository
    go(app, ISSUES)
    monkeypatch.setattr(repository, "fetch_issue", lambda client, issue_id: None)
    issue_select(app).set_value("2 - Flickering <b>lights</b>").run()
    assert not app.exception
    assert any("no longer exists" in w.value for w in app.warning)


def test_assign_failure_is_shown(app):
    go(app, ISSUES)
    app.store.fail["update"] = RuntimeError("boom")
    app.selectbox(key="technician_1").set_value("Ali").run()
    [b for b in app.button if b.key == "assign_btn_1"][0].click().run()
    assert any("Failed to assign technician" in e.value for e in app.error)
    assert [r for r in app.store.rows if r["id"] == 1][0]["assigned_to"] is None


@pytest.mark.parametrize("bad_result", [
    {"category": "HVAC"},                                                                   # missing fields
    {"category": "HVAC", "priority": "urgent", "ai_summary": "s", "suggested_action": "a"},  # bad priority
    "not json structure",
    [],
])
def test_invalid_analysis_is_not_saved(app, bad_result):
    app.ai.analyze_issue = lambda title, description: bad_result
    go(app, REPORT)
    before = len(app.store.rows)
    fill_and_submit(app)
    assert not app.exception
    assert any("not saved because the analysis failed" in e.value for e in app.error)
    assert len(app.store.rows) == before and "last_submission" not in app.session_state


def test_insert_failure_keeps_the_form_and_reports_clearly(app):
    app.store.fail["insert"] = RuntimeError("insert denied")
    go(app, REPORT)
    before = len(app.store.rows)
    fill_and_submit(app)
    assert any("could not be saved" in e.value and "insert denied" in e.value for e in app.error)
    assert len(app.store.rows) == before
    assert [t for t in app.text_input if t.label == "Issue Title"][0].value == "Water heater cold"
    assert not app.success


def test_saved_issue_is_normalised_and_department_derived(app):
    app.ai.analyze_issue = lambda title, description: {
        "category": "hvac", "priority": "high", "ai_summary": "s", "suggested_action": "a"}
    go(app, REPORT)
    fill_and_submit(app, title="  Spaced title  ")
    new = app.store.rows[0]
    assert (new["category"], new["priority"], new["department"], new["status"]) == ("HVAC", "HIGH", "Facilities", "OPEN")
    assert new["title"] == "Spaced title"


def test_whitespace_only_fields_are_rejected(app):
    go(app, REPORT)
    before = len(app.store.rows)
    fill_and_submit(app, title="   ", desc="  ", loc=" ")
    assert app.warning and len(app.store.rows) == before and not app.ai.calls


def test_load_failure_shows_error_on_every_page(app):
    app.store.fail["select"] = RuntimeError("cannot connect")
    for page in (DASH, ISSUES, ANALYTICS):
        open_page(app, page)
        assert not app.exception
        assert any("cannot connect" in e.value for e in app.error), page


def test_dashboard_and_analytics_numbers_match_records(app):
    from utils.logic import compute_metrics
    m = compute_metrics(app.store.rows)
    go(app, ANALYTICS)
    html = " ".join(x.value for x in app.markdown)
    assert f'{m["resolution_rate"]}%' in html and f'{m["high_share"]}%' in html
    assert f'>{m["unresolved"]}<' in html.replace(" ", "") or str(m["unresolved"]) in html
    go(app, DASH)
    html = " ".join(x.value for x in app.markdown)
    assert f'<div class="mm-metric-value">{m["total"]}</div>' in html
    assert f'<div class="mm-metric-value">{m["open"]}</div>' in html
    assert f'<div class="mm-metric-value">{m["resolved"]}</div>' in html


def test_empty_database_is_handled_on_all_pages(app):
    app.store.rows.clear()
    expected = {DASH: "No maintenance issues found.", ISSUES: "No maintenance issues found.",
                ANALYTICS: "No data available for analytics."}
    for page, message in expected.items():
        go(app, page)
        assert any(message == i.value for i in app.info), page
    go(app, REPORT)


# ---------------------------------------------------------------------------
# Sidebar navigation (regression: labels were invisible on some Streamlit versions)
# ---------------------------------------------------------------------------
def nav_buttons(at):
    return [b for b in at.button if b.key and b.key.startswith("navbtn_")]


def test_navigation_shows_all_four_labels(app):
    assert [b.label for b in nav_buttons(app)] == [DASH, ISSUES, REPORT, ANALYTICS]


def test_each_navigation_button_switches_page_and_marks_it_active(app):
    titles = {DASH: "Dashboard", ISSUES: "Issues", REPORT: "Report a Maintenance Issue", ANALYTICS: "Analytics"}
    for page, title in titles.items():
        open_page(app, page)
        assert app.session_state["page"] == page
        assert any(f'<h1>{title}</h1>' in m.value for m in app.markdown), page


def test_navigation_does_not_depend_on_streamlit_internals_or_hide_anything():
    from utils import theme
    css = theme._CSS
    start = css.index("/* Navigation")
    end = css.index(".mm-side-card {")
    nav_css = css[start:end]
    assert "display: none" not in nav_css and "visibility: hidden" not in nav_css
    assert "first-child" not in nav_css and "stRadio" not in nav_css and "radiogroup" not in nav_css
    import re
    assert not re.search(r"opacity:\s*0\s*;", nav_css)
    assert not re.search(r"font-size:\s*0(px|rem|em)?\s*;", nav_css)
