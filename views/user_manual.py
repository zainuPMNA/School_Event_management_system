import streamlit as st

def render():
    st.title("📖 User Manual")
    st.markdown("Welcome to the **School Event Management App**. This guide provides a comprehensive step-by-step workflow for managing your school's sports or arts events from start to finish.")
    
    st.markdown("---")
    
    with st.expander("Step 1: System Initialization & Context Setup (⚙️ Settings)", expanded=True):
        st.markdown("""
        Before you begin importing students or configuring events, you **must** configure the core rules and structure of your school's system.
        1. Navigate to **⚙️ Settings** from the sidebar.
        2. Add all **Categories** (e.g., Sub-Junior, Junior, Senior) your school uses.
        3. Add all **House Groups** (e.g., Red House, Blue House).
        4. Add all **Genders** (e.g., Boys, Girls).
        5. Define the **Point Systems** for 1st, 2nd, and 3rd places (ensure you save these for both Individual and Group event types).
        6. Upload the **School Logo** and configure the **Print Headers** (useful for generating official scoring sheets and certificates).
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
        3. Print the **Judges Scoring Sheets** from this tab. You can enable 'Automatic Layouts' or 'Manual Override' modes depending on if you want the schedule generated dynamically. The PDF sheets are highly detailed and given to field judges.
        """)
        
    with st.expander("Step 4: Live Results & Points Evaluation (🏆 Enter Scores)", expanded=False):
        st.markdown("""
        As events wrap up and score sheets are handed back, you enter them into the system here.
        1. Navigate to **🏆 Enter Scores**.
        2. Check the **Event Checklist** to see what events are pending scoring.
        3. Select a completed program and assign the **1st, 2nd, and 3rd place winners** using their Chest Numbers.
        4. The system will use your pre-configured Point Rules (from Settings) to mathematically distribute the points.
        5. **Corrections Mode**: If a typo occurred, expand the "Corrections & Overrides" section at the bottom to easily delete an incorrect score entry and re-upload the results.
        """)
        
    with st.expander("Step 5: Follow Leaderboards & Event Tracking (📊 Dashboards)", expanded=False):
        st.markdown("""
        Real-time analytics to keep track of the competition visually.
        1. Navigate to **📊 Dashboards**.
        2. The **Overall Leaderboard** highlights group/house standings.
        3. Use the **Category Champions** table to identify the "Champion of Champions" tracking highest individual aggregate scores.
        4. Utilize the **Deep Dive View** tabs for specific, granular analysis per student or program.
        """)
        
    with st.expander("Step 6: Archiving, Reports, & Certificates (🖨️ Downloads & 🏅 Certificates)", expanded=False):
        st.markdown("""
        After all scoring is completed, fulfill administrative duties.
        1. Navigate to **🏅 Certificates**.
        2. The system can generate massive batches of customizable PDF or raw DOCX word documents based on winner results.
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
        4. **Clean Slate**: Use the red danger-zone buttons to wipe your system clean so it's ready for the following year's setup.
        """)
        
    st.info("💡 **Pro Tip**: Use the **Event Mode Toggle** (Sports / Arts) in the sidebar at all times! Competitions are completely silo'd between the two. Once actual event day begins, lock the toggle using the `🔒 Lock Event Mode` checkbox to stop yourself from accidentally adding Arts points to the Sports module.")
