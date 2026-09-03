import streamlit as st
from services.database import supabase
from services.ai_service import analyze_issue

st.set_page_config(
    page_title="Maintenance Management System",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Maintenance Management System")

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

                # Save everything to Supabase
                response = supabase.table("issues").insert({
                    "title": title,
                    "description": description,
                    "location": location,
                    "category": ai_result["category"],
                    "priority": ai_result["priority"],
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

                st.write("**AI Summary:**")
                st.write(ai_result["ai_summary"])

                st.write("**Suggested Action:**")
                st.write(ai_result["suggested_action"])

            except Exception as e:
                st.error(f"❌ Failed to submit issue: {e}")