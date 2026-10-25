import streamlit as st
from views.ui import hero

def render():
    hero("User Manual", "Step-by-step guide from setup to certificates.", "📖")
    st.markdown("Welcome to the **School Event Management App**. This guide provides a comprehensive step-by-step workflow for managing your school's sports or arts events from start to finish.")
    
    st.markdown("---")
    
    with st.expander("Step 1: System Initialization & Context Setup (⚙️ Settings)", expanded=True):
        st.markdown("""
        Before you begin importing students or configuring events, you **must** configure the core rules and structure of your school's system.
        1. Navigate to **⚙️ Settings** from the sidebar.
        2. Add all **Categories** (e.g., Sub-Junior, Junior, Senior) your school uses.
        3. Add all **House Groups** (e.g., Red House, Blue House).
        4. Add all **Genders** (e.g., Boys, Girls).
        5. Define the **Point Values** for 1st, 2nd, 3rd (add 4th, 5th… if needed).
        6. Fill in **Event Info** and upload the **School Logo** — shown on the sidebar, live scoreboard, certificates and every document.
        7. *(Recommended)* Set an **Admin Password** in the 🔐 Security tab so only staff can enter scores or edit data.
        """)
        
    with st.expander("Step 2: Upload Roster & Assignations (📁 Upload & Manage Data)", expanded=False):
        st.markdown("""
        Once your settings are confirmed, you can populate the system with student and event records.
        1. Navigate to **📁 Upload & Manage Data**.
        2. **Students Tab**: Add students manually or via bulk CSV upload. *Tip: Download the CSV template, fill it out precisely, and upload it.* Ensure you click "Generate Chest Numbers" once all students are uploaded.
        3. **Programs Tab**: Add events (e.g., 100m Dash, Spelling Bee) either manually or via CSV. Notice that your events are strictly tied to the active system **Event Mode** (Sports or Arts). 
        4. **Group Teams Tab**: Use this to manually or bulk register group members. Specify the Team Leader and the list of participating students.
        5. **Individual Assignation Tab**: Directly assign an individual student to the programs they will be competing in.
        """)
        
    with st.expander("Step 3: Event Scheduling & Scoring Sheets (🗓️ Program Schedule)", expanded=False):
        st.markdown("""
        With your participants and programs locked in, it's time to physically plan the event dates and times.
        1. Navigate to **🗓️ Program Schedule**.
        2. Set specific **Dates, Times, and Venues** for each program.
        3. Pick dates and times with the calendar/clock pickers. The app warns you if two programs are at the same venue at the same time.
        4. Print **Judges' Scoring Sheets** from **🖨️ Downloads & Prints**.
        """)
        
    with st.expander("Step 4: Live Results & Points Evaluation (🏆 Enter Scores)", expanded=False):
        st.markdown("""
        As events wrap up and score sheets are handed back, you enter them into the system here.
        1. Navigate to **🏆 Enter Scores**.
        2. Programs marked ⏳ are still pending; ✅ means results are saved.
        3. **Sports**: choose the place for each finisher. **Arts**: type marks (leave blank for absentees) and the app ranks them.
        4. Points come from your Settings automatically.
        5. **Corrections**: select the program again, fix the entry and press Save — it recalculates instantly.
        """)
        
    with st.expander("Step 5: Follow Leaderboards & Event Tracking (📊 Dashboards)", expanded=False):
        st.markdown("""
        Real-time analytics to keep track of the competition visually.
        1. Navigate to **📊 Dashboards**.
        2. The **Group Leaderboard** shows an animated podium and charts of house standings.
        3. **Category-wise** shows which house leads in each category.
        4. **Individual Champions** finds the top scorers by gender and category.
        5. Open **📺 Live Scoreboard** on a projector — it refreshes on its own and celebrates new leaders with confetti.
        """)
        
    with st.expander("Step 6: Archiving, Reports, & Certificates (🖨️ Downloads & 🏅 Certificates)", expanded=False):
        st.markdown("""
        After all scoring is completed, fulfill administrative duties.
        1. Navigate to **🏅 Certificates**.
        2. Pick an event to get certificates for 1st, 2nd and 3rd place (optionally participation certificates too), then Print / Save as PDF.
        3. Navigate to **🖨️ Downloads & Prints**.
        4. Export **Winners Lists** filtered dynamically by multiple parameters (Category-wise printing or Master List outputs).
        5. Print the **Coordinators Operational Checklist** to track what still needs finalizing.
        """)
        
    with st.expander("Step 7: Backups & System Resets (💾 Data Refactory Center)", expanded=False):
        st.markdown("""
        Security operations and academic-year resets.
        1. Navigate to **💾 Data Refactory Center**.
        2. **Back up Database**: Click the download button for your `.enc` safe file. Save this daily. 
        3. **Restore Database**: Upload an `.enc` file to perfectly roll back in case of system emergencies.
        4. **Automatic Snapshots**: a copy is saved in `backups/` before every import or erase, and can be restored with one click.
        5. **Clean Slate**: Use the Erase tab to wipe the system for next year's setup.
        """)
        
    st.info("💡 **Pro Tip**: Use the **Event Mode Toggle** (Sports / Arts) in the sidebar at all times! Competitions are completely silo'd between the two. Once actual event day begins, lock the toggle using the `🔒 Lock Event Mode` checkbox to stop yourself from accidentally adding Arts points to the Sports module.")
