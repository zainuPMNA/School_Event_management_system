import html

import streamlit as st
from database import init_db, get_event_info

# Page config must be the first Streamlit command
st.set_page_config(page_title="School Event Management App", page_icon="🏅", layout="wide")

# Initialize SQLite database (also migrates older databases)
init_db()

# Lazy import views to avoid circular dependencies and issues with DB init
from views import settings, data_upload, scoring, dashboards, certificates, downloads, schedule, data_refactory, about, user_manual, live
from views.ui import inject_global_css, sidebar_login, image_data_uri


def sidebar_brand():
    school, event, year, logo = get_event_info()
    logo_uri = image_data_uri(logo)
    img = f'<img src="{logo_uri}">' if logo_uri else '<div style="font-size:2.6rem">🏅</div>'
    st.sidebar.markdown(
        f'<div class="sidebar-brand">{img}<div class="t">{html.escape(event)}</div>'
        f'<div class="s">{html.escape(school)} {html.escape(str(year))}</div></div>',
        unsafe_allow_html=True,
    )


def main():
    inject_global_css()
    sidebar_brand()

    # Event Mode Toggle & Locking
    lock_mode = st.sidebar.checkbox("🔒 Lock Event Mode", value=st.session_state.get('lock_mode', False), help="Check this to prevent accidental mode switching.")
    st.session_state['lock_mode'] = lock_mode

    current_mode_index = 0 if st.session_state.get('event_mode', 'Sports') == 'Sports' else 1
    st.session_state['event_mode'] = st.sidebar.radio(
        "Event Mode",
        ["Sports", "Arts"],
        index=current_mode_index,
        disabled=lock_mode,
        horizontal=True,
    )

    st.sidebar.markdown("---")

    pages = {
        "📺 Live Scoreboard": live.render,
        "📊 Dashboards": dashboards.render,
        "🏆 Enter Scores": scoring.render,
        "🗓️ Program Schedule": schedule.render,
        "🏅 Certificates": certificates.render,
        "📁 Upload & Manage Data": data_upload.render,
        "💾 Data Refactory Center": data_refactory.render,
        "⚙️ Settings": settings.render,
        "🖨️ Downloads & Prints": downloads.render,
        "📖 User Manual": user_manual.render,
        "ℹ️ About": about.render
    }

    selection = st.sidebar.radio("Navigation", list(pages.keys()), index=1)

    st.sidebar.markdown("---")
    sidebar_login()

    # Render the selected page
    pages[selection]()


if __name__ == "__main__":
    main()
