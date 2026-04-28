import streamlit as st

def render():
    st.title("ℹ️ About")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("School Event Management App")
        st.markdown("""
        This application is designed to digitally manage and automate school event workflows.
        It comprehensively handles everything from individual and group student registrations, 
        schedule orchestration, real-time results scoring, and dynamic point leaderboards,
        down to automated certificate and report generation.
        
        Whether operating in Sports Mode or Arts Mode, the system provides a robust offline-capable 
        architecture to smoothly run your organization's events.
        """)

        st.markdown("---")
        st.markdown("#### System Information")
        st.markdown("**Version:** v1.0.0 (Stable Release)")
        st.markdown("**Core Technologies:** Python 3")
        st.markdown("**Frameworks & Libraries:** Streamlit, Pandas, ReportLab, DocxTemplate")
        st.markdown("**Database:** SQLite3")
        
        st.markdown("---")
        st.markdown("#### Developer & Copyright")
        st.markdown("**Created, Architected & Maintained by:** ZAIN™")
        st.error("🔒 **PROTECTED ATTRIBUTION:** The developer name (**ZAIN™**) is permanently hardcoded and legally protected. It cannot be removed, altered, or deleted under the software's core licensing terms.")
        st.markdown("*© All rights reserved.*")
        
    with col2:
        st.info("💡 **Tip:** Use the 'Lock Event Mode' feature in the sidebar during active event days to prevent accidental point mixing.")
