#app.py
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# set_page_config must be the first Streamlit command
st.set_page_config(
    page_title="FacilityFlow",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="auto"
)

# Service imports. If credentials are missing (.env not found) show a clear
# message instead of a raw traceback.
try:
    from services.database import supabase
    from services.ai_service import analyze_issue, MODEL
except Exception as e:
    st.error(f"❌ The app could not start: {e}")
    st.info(
        "Make sure a `.env` file exists next to `app.py` with your Supabase "
        "and Gemini credentials, then restart the app."
    )
    st.stop()

from utils import repository, theme
from utils.logic import (
    PRIORITIES, STATUS_OPTIONS, TECHNICIANS, UNASSIGNED,
    compute_metrics, count_by, department_for_category, display_value, ensure_option,
    filter_issues, filter_options, norm, percent, resolve_department, resolve_technician,
    validate_ai_result,
)

# Sidebar navigation
NAV_DASHBOARD = "📊  Dashboard"
NAV_ISSUES = "📋  Issues"
NAV_REPORT = "➕  Report Issue"
NAV_ANALYTICS = "📈  Analytics"
NAV_OPTIONS = [NAV_DASHBOARD, NAV_ISSUES, NAV_REPORT, NAV_ANALYTICS]

# Columns shown in the issue tables
TABLE_COLUMNS = [
    "id", "title", "location", "category", "priority",
    "department", "status", "assigned_to", "created_at"
]
DASHBOARD_COLUMNS = [
    "id", "title", "location", "category", "priority", "status", "assigned_to", "created_at"
]
# Fixed pixel widths keep the tables compact (no clipped last column on a normal screen)
COLUMN_LABELS = {
    "id": st.column_config.NumberColumn("ID", width=52),
    "title": st.column_config.TextColumn("Title", width=195),
    "location": st.column_config.TextColumn("Location", width=105),
    "category": st.column_config.TextColumn("Category", width=92),
    "priority": st.column_config.TextColumn("Priority", width=84),
    "department": st.column_config.TextColumn("Department", width=112),
    "status": st.column_config.TextColumn("Status", width=104),
    "assigned_to": st.column_config.TextColumn("Assigned To", width=100),
    "created_at": st.column_config.TextColumn("Created (UTC)", width=128),
}

FILTER_KEYS = {
    "search": "f_search",
    "category": "f_category",
    "priority": "f_priority",
    "status": "f_status",
    "department": "f_department",
    "technician": "f_technician",
}


# ---------------------------------------------------------------------------
# Table helpers (display only, nothing here writes to the database)
# ---------------------------------------------------------------------------
def build_table(issues, columns):
    rows = []
    for issue in issues:
        row = {}
        for col in columns:
            if col == "id":
                row[col] = issue.get("id")
            elif col == "created_at":
                row[col] = issue.get("created_at")
            elif col == "department":
                row[col] = resolve_department(issue)
            elif col == "assigned_to":
                row[col] = resolve_technician(issue)
            elif col in ("priority", "status"):
                row[col] = norm(issue.get(col)) or "N/A"
            else:
                row[col] = str(display_value(issue.get(col)))
        rows.append(row)

    df = pd.DataFrame(rows, columns=columns)
    if "created_at" in df.columns:
        stamps = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        df["created_at"] = stamps.dt.strftime("%b %d, %Y %H:%M").fillna("N/A")
    return df


def style_table(df):
    """Colour the priority and status columns."""
    def colour(mapping):
        def _inner(value):
            colour_hex = mapping.get(str(value).upper())
            if not colour_hex:
                return "color: #94A3B8"
            return f"color: {colour_hex}; font-weight: 600"
        return _inner

    styler = df.style
    apply_map = getattr(styler, "map", None) or styler.applymap
    if "priority" in df.columns:
        styler = apply_map(colour(theme.PRIORITY_COLORS), subset=["priority"])
        apply_map = getattr(styler, "map", None) or styler.applymap
    if "status" in df.columns:
        styler = apply_map(colour(theme.STATUS_COLORS), subset=["status"])
    return styler


def show_table(issues, columns):
    df = build_table(issues, columns)
    st.dataframe(
        style_table(df),
        column_config={c: COLUMN_LABELS[c] for c in columns},
        width="stretch",
        hide_index=True
    )


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def donut_chart(counts, colour_map, height=290):
    labels = list(counts.keys())
    values = list(counts.values())
    colours = [colour_map.get(str(l).upper(), theme.UNKNOWN_COLOR) for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.66,
        marker=dict(colors=colours, line=dict(color="#111827", width=3)),
        textinfo="value",
        textfont=dict(color="#F9FAFB", size=13),
        sort=False,
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>"
    ))
    fig.add_annotation(
        text=f"<b>{sum(values)}</b><br><span style='font-size:11px;color:#94A3B8'>issues</span>",
        showarrow=False, font=dict(size=24, color="#F9FAFB")
    )
    fig.update_layout(legend=dict(orientation="h", y=-0.06, x=0.5, xanchor="center"))
    return theme.style_figure(fig, height)


def bar_chart(counts, colour, height=300):
    items = sorted(counts.items(), key=lambda kv: kv[1])  # largest ends up on top
    fig = go.Figure(go.Bar(
        x=[v for _, v in items],
        y=[k for k, _ in items],
        orientation="h",
        marker=dict(color=colour, cornerradius=6),
        text=[v for _, v in items],
        textposition="outside",
        textfont=dict(color="#CBD5E1"),
        hovertemplate="%{y}: %{x}<extra></extra>"
    ))
    fig.update_xaxes(showgrid=True, dtick=1, rangemode="tozero")
    fig.update_yaxes(showgrid=False)
    fig.update_layout(bargap=0.35)
    return theme.style_figure(fig, height)


def chart_panel(title, subtitle, fig):
    with st.container(border=True):
        theme.render(f'<div class="mm-panel-title">{theme.esc(title)}</div>')
        if subtitle:
            theme.render(f'<div class="mm-panel-sub">{theme.esc(subtitle)}</div>')
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Shared pieces
# ---------------------------------------------------------------------------
def metric_cards(issues):
    m = compute_metrics(issues)

    def share(n):
        return f"{percent(n, m['total'])}% of all issues" if m["total"] else "No issues yet"

    theme.metric_row([
        theme.metric_card("Total Issues", m["total"], "list", theme.ACCENT, "All reported issues"),
        theme.metric_card("Open Issues", m["open"], "alert", "#3B82F6", share(m["open"])),
        theme.metric_card("High Priority", m["high"], "flame", "#EF4444", share(m["high"])),
        theme.metric_card("Resolved Issues", m["resolved"], "check", "#22C55E", share(m["resolved"])),
    ])


def analysis_cards(summary, action):
    col1, col2 = st.columns(2)
    with col1:
        theme.render(theme.ai_card("Summary", summary, theme.ACCENT))
    with col2:
        theme.render(theme.ai_card("Suggested Action", action, theme.ACCENT_ALT))


def analysis_panel(category, priority, department, summary, action):
    """Analysis result shown right after an issue was submitted."""
    chips = (
        '<div class="mm-ai-chips">'
        f'<span class="mm-chip-label">Category</span>{theme.badge(category, "category")}'
        f'<span class="mm-chip-label">Priority</span>{theme.badge(priority, "priority")}'
        f'<span class="mm-chip-label">Department</span>{theme.badge(department, "department")}'
        '</div>'
    )
    with st.container(border=True):
        theme.render('<div class="mm-panel-title">Automated Analysis</div>')
        theme.render(chips)
        analysis_cards(summary, action)


def reset_filters():
    """Callback for the 'Clear filters' button."""
    st.session_state[FILTER_KEYS["search"]] = ""
    for name, key in FILTER_KEYS.items():
        if name != "search":
            st.session_state[key] = "All"


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_dashboard(issues, error):
    theme.page_header("Dashboard", "Live overview of maintenance activity.")

    if error:
        st.error(f"❌ Failed to load dashboard: {error}")
        return

    metric_cards(issues)

    theme.section_title("Recent Issues", "Latest 8 reports")
    if not issues:
        st.info("No maintenance issues found.")
        return
    show_table(issues[:8], DASHBOARD_COLUMNS)

    col1, col2 = st.columns(2)
    with col1:
        chart_panel(
            "Priority breakdown", "How urgent the reported issues are",
            donut_chart(count_by(issues, "priority", PRIORITIES), theme.PRIORITY_COLORS)
        )
    with col2:
        chart_panel(
            "Status breakdown", "Where issues are in the workflow",
            donut_chart(count_by(issues, "status", STATUS_OPTIONS), theme.STATUS_COLORS)
        )


def page_issues(issues, error):
    theme.page_header("Issues", "Search, review and manage reported maintenance issues.")

    if error:
        st.error(f"❌ Failed to load issues: {error}")
        return

    if not issues:
        st.info("No maintenance issues found.")
        return

    # --- Filters ---
    with st.container(border=True):
        search_col, clear_col = st.columns([5, 1], vertical_alignment="bottom")
        with search_col:
            search = st.text_input(
                "🔎 Search",
                placeholder="Search title, description or location...",
                key=FILTER_KEYS["search"]
            )
        with clear_col:
            st.button("Clear filters", on_click=reset_filters, width="stretch")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            category_filter = st.selectbox(
                "📂 Category",
                ["All"] + filter_options(issues, "category"),
                key=FILTER_KEYS["category"]
            )
        with c2:
            priority_filter = st.selectbox(
                "⚡ Priority",
                ["All"] + filter_options(issues, "priority", PRIORITIES),
                key=FILTER_KEYS["priority"]
            )
        with c3:
            status_filter = st.selectbox(
                "📌 Status",
                ["All"] + filter_options(issues, "status", STATUS_OPTIONS),
                key=FILTER_KEYS["status"]
            )
        with c4:
            department_filter = st.selectbox(
                "🏢 Department",
                ["All"] + filter_options(issues, "department"),
                key=FILTER_KEYS["department"]
            )
        with c5:
            technician_filter = st.selectbox(
                "👷 Technician",
                ["All"] + filter_options(issues, "assigned_to", TECHNICIANS),
                key=FILTER_KEYS["technician"]
            )

    filtered_issues = filter_issues(
        issues, search, category_filter, priority_filter, status_filter,
        department_filter, technician_filter
    )

    theme.section_title("All Issues", f"{len(filtered_issues)} of {len(issues)} shown")
    if not filtered_issues:
        st.info("No issues match the selected search and filters. Try clearing some filters.")
        return
    show_table(filtered_issues, TABLE_COLUMNS)

    theme.section_title("Issue Details")

    issue_options = {
        f"{issue['id']} - {display_value(issue.get('title'), 'Untitled issue')}": issue["id"]
        for issue in filtered_issues
    }

    selected_issue = st.selectbox("Select an issue", list(issue_options.keys()))
    selected_id = issue_options[selected_issue]

    try:
        detail = repository.fetch_issue(supabase, selected_id)
    except Exception as e:
        st.error(f"❌ Failed to load issue details: {e}")
        return

    if detail is None:
        st.warning("This issue no longer exists. Use the Refresh button to reload the list.")
        return

    # Safe display values (NULL / empty values never crash the page)
    title_text = display_value(detail.get("title"), "Untitled issue")
    location_text = display_value(detail.get("location"))
    category_text = display_value(detail.get("category"))
    priority_text = norm(detail.get("priority")) or "N/A"
    department_text = resolve_department(detail)
    status_text = norm(detail.get("status")) or "N/A"
    assigned_text = resolve_technician(detail)
    description_raw = detail.get("description")

    # --- Issue Information ---
    with st.container(border=True):
        fields = "".join([
            theme.info_field("Category", theme.badge(category_text, "category")),
            theme.info_field("Priority", theme.badge(priority_text, "priority")),
            theme.info_field("Department", theme.esc(department_text)),
            theme.info_field("Status", theme.badge(status_text, "status")),
            theme.info_field("Assigned To", theme.esc(assigned_text)),
        ])
        theme.render(
            f'<div class="mm-issue-title">{theme.esc(title_text)}</div>'
            f'<div class="mm-issue-loc">📍 {theme.esc(location_text)}</div>'
            f'<div class="mm-fields">{fields}</div>'
        )

    # --- Description ---
    with st.container(border=True):
        theme.render('<div class="mm-panel-title">📝 Description</div>')
        theme.render(theme.text_block(
            display_value(description_raw, "No description provided."),
            empty_hint=not str(description_raw or "").strip()
        ))

    # --- Automated analysis ---
    with st.container(border=True):
        theme.render('<div class="mm-panel-title">Automated Analysis</div>')
        analysis_cards(
            display_value(detail.get("ai_summary"), "No summary available."),
            display_value(detail.get("suggested_action"), "No suggested action available.")
        )

    # --- Manage Issue ---
    theme.section_title("Manage Issue")

    with st.container(border=True):
        manage_col1, manage_col2 = st.columns(2)

        # Assign Technician
        with manage_col1:
            theme.render('<div class="mm-panel-title">👷 Assign Technician</div>')

            technician_options, technician_index = ensure_option(
                TECHNICIANS, resolve_technician(detail)
            )
            new_technician = st.selectbox(
                "Technician",
                technician_options,
                index=technician_index,
                key=f"technician_{selected_id}"
            )

            if st.button("Assign Technician", key=f"assign_btn_{selected_id}", type="primary"):
                try:
                    repository.update_issue(supabase, selected_id, {
                        "assigned_to": None if new_technician == UNASSIGNED else new_technician
                    })
                    st.session_state["flash"] = "✅ Technician assigned successfully!"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to assign technician: {e}")

        # Update Status
        with manage_col2:
            theme.render('<div class="mm-panel-title">🔄 Update Status</div>')

            status_options, status_index = ensure_option(STATUS_OPTIONS, detail.get("status"))
            new_status = st.selectbox(
                "Change Status",
                status_options,
                index=status_index,
                key=f"status_{selected_id}"
            )

            if st.button("Update Status", key=f"status_btn_{selected_id}", type="primary"):
                try:
                    repository.update_issue(supabase, selected_id, {"status": new_status})
                    st.session_state["flash"] = "✅ Status updated successfully!"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to update status: {e}")


def page_report():
    theme.page_header(
        "Report a Maintenance Issue",
        "Describe the problem. Gemini analyses it to suggest a category, priority and recommended action."
    )

    # Result of the last submission (kept across the rerun that refreshes the sidebar)
    last = st.session_state.get("last_submission")
    if last:
        st.success("✅ Maintenance issue submitted successfully!")
        analysis_panel(
            last["category"], last["priority"], last["department"],
            last["ai_summary"], last["suggested_action"]
        )
        st.write("")

    # The form key changes after every successful submit, which gives a fresh,
    # empty form (prevents accidentally submitting the same issue twice).
    nonce = st.session_state.get("form_nonce", 0)

    with st.form(f"issue_form_{nonce}"):
        title = st.text_input(
            "Issue Title",
            placeholder="e.g. AC not working",
            key=f"issue_title_{nonce}"
        )
        description = st.text_area(
            "Describe the issue",
            placeholder="Explain what is wrong...",
            height=160,
            key=f"issue_description_{nonce}"
        )
        location = st.text_input(
            "Location",
            placeholder="e.g. Lab 3",
            key=f"issue_location_{nonce}"
        )

        submitted = st.form_submit_button("Submit Issue", type="primary")

        if not submitted:
            return

        title, description, location = title.strip(), description.strip(), location.strip()
        if not title or not description or not location:
            st.warning("Please fill in all fields.")
            return

        # Step 1: automated analysis. If this fails, nothing is saved.
        try:
            with st.spinner("Analyzing the issue..."):
                ai_result = validate_ai_result(
                    analyze_issue(title=title, description=description)
                )
        except Exception as e:
            st.error(
                f"❌ The issue was not saved because the analysis failed: {e}. "
                "Please try again."
            )
            return

        # Step 2: save to Supabase (department is derived from the category)
        department = department_for_category(ai_result["category"])
        try:
            repository.insert_issue(supabase, {
                "title": title,
                "description": description,
                "location": location,
                "category": ai_result["category"],
                "priority": ai_result["priority"],
                "department": department,
                "ai_summary": ai_result["ai_summary"],
                "suggested_action": ai_result["suggested_action"],
                "status": "OPEN"
            })
        except Exception as e:
            st.error(f"❌ The analysis worked, but the issue could not be saved: {e}")
            return

        # Show the result after a rerun so the sidebar counts refresh too
        st.session_state["last_submission"] = {
            "category": ai_result["category"],
            "priority": ai_result["priority"],
            "department": department,
            "ai_summary": ai_result["ai_summary"],
            "suggested_action": ai_result["suggested_action"],
        }
        st.session_state["form_nonce"] = nonce + 1
        st.rerun()


def page_analytics(issues, error):
    theme.page_header("Analytics", "Trends across categories, priorities, statuses and departments.")

    if error:
        st.error(f"❌ Failed to load analytics: {error}")
        return

    if not issues:
        st.info("No data available for analytics.")
        return

    m = compute_metrics(issues)
    theme.metric_row([
        theme.metric_card("Resolution Rate", f"{m['resolution_rate']}%", "percent", "#22C55E",
                          f"{m['resolved']} of {m['total']} resolved"),
        theme.metric_card("Unresolved", m["unresolved"], "alert", "#3B82F6", "Not yet resolved"),
        theme.metric_card("High Priority Share", f"{m['high_share']}%", "flame", "#EF4444",
                          f"{m['high']} high priority"),
        theme.metric_card("Unassigned", m["unassigned"], "user", "#F59E0B", "No technician yet"),
    ])

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        chart_panel("Issues by Category", "", bar_chart(count_by(issues, "category"), theme.ACCENT))
    with col2:
        chart_panel("Issues by Priority", "",
                    donut_chart(count_by(issues, "priority", PRIORITIES), theme.PRIORITY_COLORS))

    col1, col2 = st.columns(2)
    with col1:
        chart_panel("Issues by Status", "",
                    donut_chart(count_by(issues, "status", STATUS_OPTIONS), theme.STATUS_COLORS))
    with col2:
        chart_panel("Issues by Department", "",
                    bar_chart(count_by(issues, "department"), theme.ACCENT_ALT))


# ---------------------------------------------------------------------------
# App shell
# ---------------------------------------------------------------------------
theme.inject_css()

# Load issues once per run (every page reads from this)
try:
    all_issues = repository.fetch_issues(supabase)
    load_error = None
except Exception as e:
    all_issues = []
    load_error = e

NAV_ITEMS = [
    (NAV_DASHBOARD, "dashboard"),
    (NAV_ISSUES, "issues"),
    (NAV_REPORT, "report"),
    (NAV_ANALYTICS, "analytics"),
]


def go_to(target):
    """Button callback: switch page (runs before the script reruns)."""
    st.session_state["page"] = target


if st.session_state.get("page") not in NAV_OPTIONS:
    st.session_state["page"] = NAV_DASHBOARD
page = st.session_state["page"]

with st.sidebar:
    theme.sidebar_brand()
    theme.sidebar_label("Navigation")
    for label, slug in NAV_ITEMS:
        # The container key drives the styling (see utils/theme.py); the active page gets its own key.
        with st.container(key=f"{'navactive' if label == page else 'nav'}_{slug}"):
            st.button(label, key=f"navbtn_{slug}", on_click=go_to, args=(label,), width="stretch")

    theme.sidebar_label("Quick Stats")
    if load_error:
        theme.render('<div class="mm-side-card"><div class="mm-side-row">Data unavailable</div></div>')
    else:
        stats = compute_metrics(all_issues)
        theme.render(
            '<div class="mm-side-card">'
            f'<div class="mm-side-row"><span>Total issues</span><b>{stats["total"]}</b></div>'
            f'<div class="mm-side-row"><span>Open</span><b>{stats["open"]}</b></div>'
            f'<div class="mm-side-row"><span>High priority</span><b>{stats["high"]}</b></div>'
            '</div>'
        )

    st.write("")
    st.button("🔄  Refresh data", width="stretch")

    theme.render(
        f'<div class="mm-side-foot">Analysis model<br><code>{theme.esc(MODEL)}</code></div>'
    )

# The "last submission" panel only belongs on the Report page
if page != NAV_REPORT:
    st.session_state.pop("last_submission", None)

# Show a success message left over from an update (before rerun)
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

if page == NAV_DASHBOARD:
    page_dashboard(all_issues, load_error)
elif page == NAV_ISSUES:
    page_issues(all_issues, load_error)
elif page == NAV_REPORT:
    page_report()
else:
    page_analytics(all_issues, load_error)
