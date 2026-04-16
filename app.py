import streamlit as st
from database import init_db

# Page config must be the first Streamlit command
st.set_page_config(page_title="School Event Management App", page_icon="🏅", layout="wide")

# Initialize SQLite database
init_db()

# Lazy import views to avoid circular dependencies and issues with DB init
from views import settings, data_upload, scoring, dashboards, certificates, downloads, schedule, data_refactory, about

def main():
    st.sidebar.title("🏅 Event Manager")
    
    # Event Mode Toggle & Locking
    lock_mode = st.sidebar.checkbox("🔒 Lock Event Mode", value=st.session_state.get('lock_mode', False), help="Check this to prevent accidental mode switching.")
    st.session_state['lock_mode'] = lock_mode
    
    current_mode_index = 0 if st.session_state.get('event_mode', 'Sports') == 'Sports' else 1
    st.session_state['event_mode'] = st.sidebar.radio(
        "Event Mode", 
        ["Sports", "Arts"], 
        index=current_mode_index,
        disabled=lock_mode
    )
    
    st.sidebar.markdown("---")
    
    pages = {
        "📊 Dashboards": dashboards.render,
        "🏆 Enter Scores": scoring.render,
        "🗓️ Program Schedule": schedule.render,
        "🏅 Certificates": certificates.render,
        "📁 Upload & Manage Data": data_upload.render,
        "💾 Data Refactory Center": data_refactory.render,
        "⚙️ Settings": settings.render,
        "🖨️ Downloads & Prints": downloads.render,
        "ℹ️ About": about.render
    }
    
    selection = st.sidebar.radio("Navigation", list(pages.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.info("Select an option above to manage your sports event data.")
    
    # Render the selected page
    pages[selection]()

if __name__ == "__main__":
    main()
