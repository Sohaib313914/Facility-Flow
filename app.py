import streamlit as st
from services.database import supabase
from services.ai_service import analyze_issue

STATUS_OPTIONS = ["OPEN", "IN PROGRESS", "RESOLVED"]

# Technicians are hardcoded for now; in the future they can be fetched from the database
TECHNICIANS = [
    "Ali",
    "Ahmed",
    "Usman",
    "Hamza",
    "Unassigned"
]

# Maps the issue category to the department responsible for it. In the future
# this can be used to notify the right department when a new issue is reported.
DEPARTMENT_MAP = {
    "HVAC": "Facilities",
    "Electrical": "Electrical",
    "Plumbing": "Facilities",
    "IT": "IT",
    "Equipment": "Maintenance",
    "Furniture": "Facilities",
    "Safety": "Safety",
    "Other": "General Maintenance"
}
DEPARTMENT_LOOKUP = {k.lower(): v for k, v in DEPARTMENT_MAP.items()}

st.set_page_config(
    page_title="Maintenance Management System",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Maintenance Management System")

# Show a success message left over from a status update (before rerun)
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

# Dashboard
st.subheader("📊 Dashboard")

try:

    response = supabase.table("issues").select("*").execute()
    issues = response.data

    total_issues = len(issues)

    open_issues = sum(
        1 for issue in issues
        if issue["status"] == "OPEN"
    )

    high_priority = sum(
        1 for issue in issues
        if issue["priority"] == "HIGH"
    )

    resolved_issues = sum(
        1 for issue in issues
        if issue["status"] == "RESOLVED"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Issues", total_issues)

    with col2:
        st.metric("Open Issues", open_issues)

    with col3:
        st.metric("High Priority", high_priority)

    with col4:
        st.metric("Resolved Issues", resolved_issues)

except Exception as e:
    st.error(f"❌ Failed to load dashboard: {e}")

st.divider()

# Recent Issues
st.subheader("📋 Recent Issues")

try:

    response = (
        supabase
        .table("issues")
        .select("id, title, location, category, priority, department, status, assigned_to, created_at")
        .order("created_at", desc=True)
        .execute()
    )

    issues = response.data

    if issues:

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search = st.text_input(
                "🔎 Search",
                placeholder="Search issue..."
            )

        with col2:
            categories = sorted(
                set(
                    issue["category"]
                    for issue in issues
                    if issue["category"]
                )
            )

            category_filter = st.selectbox(
                "📂 Category",
                ["All"] + categories
            )

        with col3:
            priority_filter = st.selectbox(
                "⚡ Priority",
                ["All", "HIGH", "MEDIUM", "LOW"]
            )

        with col4:
            status_filter = st.selectbox(
                "📌 Status",
                ["All"] + STATUS_OPTIONS
            )

        filtered_issues = issues

        if search:
            filtered_issues = [
                issue for issue in filtered_issues
                if search.lower() in issue["title"].lower()
            ]

        if category_filter != "All":
            filtered_issues = [
                issue for issue in filtered_issues
                if issue["category"] == category_filter
            ]

        if priority_filter != "All":
            filtered_issues = [
                issue for issue in filtered_issues
                if issue["priority"] == priority_filter
            ]

        if status_filter != "All":
            filtered_issues = [
                issue for issue in filtered_issues
                if issue["status"] == status_filter
            ]

        st.dataframe(
            filtered_issues,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("🔍 Issue Details")

        if filtered_issues:

            issue_options = {
                f"{issue['id']} - {issue['title']}": issue["id"]
                for issue in filtered_issues
            }

            selected_issue = st.selectbox(
                "Select an issue",
                list(issue_options.keys())
            )

            selected_id = issue_options[selected_issue]

            detail_response = (
                supabase
                .table("issues")
                .select("*")
                .eq("id", selected_id)
                .execute()
            )

            if detail_response.data:
                detail = detail_response.data[0]

                st.write(f"**Title:** {detail['title']}")
                st.write(f"**Location:** {detail['location']}")
                st.write(f"**Category:** {detail['category']}")
                st.write(f"**Priority:** {detail['priority']}")
                st.write(f"**Department:** {detail.get('department') or 'N/A'}")
                st.write(f"**Status:** {detail['status']}")
                st.write(f"**Assigned To:** {detail.get('assigned_to') or 'Unassigned'}")
                st.write(f"**Description:** {detail['description']}")
                st.write(f"**AI Summary:** {detail['ai_summary']}")
                st.write(f"**Suggested Action:** {detail['suggested_action']}")

                st.write("### Technician Assignment")

                current_technician = detail.get("assigned_to") or "Unassigned"

                technician_index = (
                    TECHNICIANS.index(current_technician)
                    if current_technician in TECHNICIANS
                    else 0
                )

                new_technician = st.selectbox(
                    "Assign Technician",
                    TECHNICIANS,
                    index=technician_index,
                    key=f"technician_{selected_id}"
                )

                if st.button("Assign Technician"):

                    try:

                        assigned_value = (
                            None
                            if new_technician == "Unassigned"
                            else new_technician
                        )

                        supabase.table("issues").update({
                            "assigned_to": assigned_value
                        }).eq("id", selected_id).execute()

                        st.session_state["flash"] = (
                            "✅ Technician assigned successfully!"
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Failed to assign technician: {e}")

                st.write("### Update Status")

                current_status = detail["status"]
                status_index = (
                    STATUS_OPTIONS.index(current_status)
                    if current_status in STATUS_OPTIONS
                    else 0
                )

                new_status = st.selectbox(
                    "Change Status",
                    STATUS_OPTIONS,
                    index=status_index,
                    key=f"status_{selected_id}"
                )

                if st.button("Update Status"):

                    try:

                        supabase.table("issues").update({
                            "status": new_status
                        }).eq("id", selected_id).execute()

                        st.session_state["flash"] = (
                            "✅ Status updated successfully!"
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Failed to update status: {e}")

        else:
            st.info("No issues match the selected filters.")

    else:
        st.info("No maintenance issues found.")

except Exception as e:
    st.error(f"❌ Failed to load recent issues: {e}")

st.divider()

# Report Issue
st.subheader("Report a Maintenance Issue")

with st.form("issue_form"):

    title = st.text_input(
        "Issue Title",
        placeholder="e.g. AC not working"
    )

    description = st.text_area(
        "Describe the issue",
        placeholder="Explain what is wrong..."
    )

    location = st.text_input(
        "Location",
        placeholder="e.g. Lab 3"
    )

    submitted = st.form_submit_button("Submit Issue")

    if submitted:

        if not title or not description or not location:
            st.warning("Please fill in all fields.")

        else:
            try:

                # AI Analysis
                with st.spinner("🤖 AI is analyzing the issue..."):

                    ai_result = analyze_issue(
                        title=title,
                        description=description
                    )

                # Determine department from AI category
                department = DEPARTMENT_LOOKUP.get(
                    str(ai_result["category"]).strip().lower(),
                    "General Maintenance"
                )

                # Save everything to Supabase
                response = supabase.table("issues").insert({
                    "title": title,
                    "description": description,
                    "location": location,
                    "category": ai_result["category"],
                    "priority": ai_result["priority"],
                    "department": department,
                    "ai_summary": ai_result["ai_summary"],
                    "suggested_action": ai_result["suggested_action"],
                    "status": "OPEN"
                }).execute()

                st.success(
                    "✅ Maintenance issue submitted successfully!"
                )

                # Display AI result
                st.subheader("🤖 AI Analysis")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Category:**")
                    st.info(ai_result["category"])

                with col2:
                    st.write("**Priority:**")
                    st.warning(ai_result["priority"])

                st.write("**Assigned Department:**")
                st.info(department)

                st.write("**AI Summary:**")
                st.write(ai_result["ai_summary"])

                st.write("**Suggested Action:**")
                st.write(ai_result["suggested_action"])

            except Exception as e:
                st.error(f"❌ Failed to submit issue: {e}")

                st.divider()

# Analytics
st.subheader("📈 Analytics")

try:

    analytics_response = (
        supabase
        .table("issues")
        .select("category, priority, status, department")
        .execute()
    )

    analytics_issues = analytics_response.data

    if analytics_issues:

        col1, col2 = st.columns(2)

        with col1:

            st.write("### Issues by Category")

            category_counts = {}

            for issue in analytics_issues:
                category = issue["category"] or "Unknown"

                category_counts[category] = (
                    category_counts.get(category, 0) + 1
                )

            st.bar_chart(category_counts)


        with col2:

            st.write("### Issues by Priority")

            priority_counts = {}

            for issue in analytics_issues:
                priority = issue["priority"] or "Unknown"

                priority_counts[priority] = (
                    priority_counts.get(priority, 0) + 1
                )

            st.bar_chart(priority_counts)


        col1, col2 = st.columns(2)

        with col1:

            st.write("### Issues by Status")

            status_counts = {}

            for issue in analytics_issues:
                status = issue["status"] or "Unknown"

                status_counts[status] = (
                    status_counts.get(status, 0) + 1
                )

            st.bar_chart(status_counts)


        with col2:

            st.write("### Issues by Department")

            department_counts = {}

            for issue in analytics_issues:
                department = issue["department"] or "Unknown"

                department_counts[department] = (
                    department_counts.get(department, 0) + 1
                )

            st.bar_chart(department_counts)

    else:
        st.info("No data available for analytics.")

except Exception as e:
    st.error(f"❌ Failed to load analytics: {e}")