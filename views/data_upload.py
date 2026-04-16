import streamlit as st
import pandas as pd
from database import get_connection, run_query, execute_query

def render():
    st.title("📁 Upload & Manage Data")
    st.markdown("Use this section to add Students and Event Programs to your database. You can add them one by one manually, or upload an Excel/CSV file for bulk import.")
    current_mode = st.session_state.get('event_mode', 'Sports')

    # Fetch lookup data for dropdowns
    try:
        categories = run_query("SELECT name FROM categories")['name'].tolist()
        genders = run_query("SELECT name FROM genders")['name'].tolist()
        groups = run_query("SELECT name FROM groups")['name'].tolist()
    except Exception as e:
        st.error("Database connection error. Have you run init_db yet?")
        categories, genders, groups = [], [], []

    tab1, tab2, tab3, tab4 = st.tabs(["🧍 Students Data", "🏃 Programs / Events Data", "👥 Group Teams Data", "🎯 Individual Assignation"])

    # ------------------ STUDENTS TAB ------------------
    with tab1:
        st.subheader("Add Students")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("📝 Manual Entry", expanded=False):
                with st.form("student_form"):
                    s_name = st.text_input("Name")
                    
                    c_left, c_right = st.columns(2)
                    with c_left:
                        s_class = st.text_input("Class")
                    with c_right:
                        s_division = st.text_input("Division")
                        
                    s_gender = st.selectbox("Gender", genders)
                    s_category = st.selectbox("Category", categories)
                    s_group = st.selectbox("Group / House", groups)
                    s_submitted = st.form_submit_button("Add Student")
                    
                    if s_submitted:
                        if s_name:
                            execute_query(
                                "INSERT INTO students (name, class_name, division, gender, category, group_name) VALUES (?, ?, ?, ?, ?, ?)",
                                (s_name, s_class, s_division, s_gender, s_category, s_group)
                            )
                            st.success(f"Added student: {s_name}")
                        else:
                            st.warning("Please enter a name.")

        with col2:
            with st.expander("📄 Bulk Upload (Excel/CSV)", expanded=False):
                st.info("Your file should have columns: Name, Class, Division, Gender, Category, Group. (Column names are case-insensitive).")
                uploaded_student_file = st.file_uploader("Upload Student List", type=['xlsx', 'csv'], key='student_file')
                if uploaded_student_file is not None:
                    try:
                        if uploaded_student_file.name.endswith('.csv'):
                            df_s = pd.read_csv(uploaded_student_file)
                        else:
                            df_s = pd.read_excel(uploaded_student_file)
                        
                        # Normalize column names
                        df_s.columns = df_s.columns.str.lower().str.strip()
                        # Map to our db columns
                        mapping = {'name': 'name', 'class': 'class_name', 'division': 'division', 'gender': 'gender', 'category': 'category', 'group': 'group_name'}
                        df_s = df_s.rename(columns=mapping)
                        
                        # Filter to only DB columns
                        db_cols = ['name', 'class_name', 'division', 'gender', 'category', 'group_name']
                        df_tocreate = df_s[[c for c in db_cols if c in df_s.columns]]
                        
                        if st.button("Confirm & Upload Students"):
                            conn = get_connection()
                            df_tocreate.to_sql('students', conn, if_exists='append', index=False)
                            conn.close()
                            st.success(f"Successfully uploaded {len(df_tocreate)} students!")
                            
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

        # Show current students
        st.markdown("---")
        st.subheader("Current Students Database")
        st.caption("You can edit or delete rows directly below and press save.")
        df_students = run_query("SELECT id, name, class_name, division, gender, category, group_name, chest_number FROM students")
        edited_students = st.data_editor(df_students, hide_index=True, use_container_width=True, num_rows="dynamic", key="student_editor")
        if st.button("Save Changes to Students", key="btn_save_students"):
            # Clean delete & replace logic similar to settings
            conn = get_connection()
            conn.execute("DELETE FROM students")
            conn.commit()
            edited_students.to_sql("students", conn, if_exists='append', index=False)
            conn.close()
            st.success("Student database updated.")
            
        st.markdown("---")
        st.subheader("🔢 Assign Chest Numbers")
        st.markdown("Automatically assign sequential 3-digit chest numbers. Each group gets a distinct 100-number block (e.g., Group A: 100+, Group B: 200+).")
        if st.button("Generate Chest Numbers"):
            conn = get_connection()
            grp_df = pd.read_sql_query("SELECT name FROM groups", conn)
            groups_list = grp_df['name'].tolist()
            
            base_allocations = {g: (i+1)*100 for i, g in enumerate(groups_list)}
            stud_df = pd.read_sql_query("SELECT id, group_name FROM students ORDER BY name ASC", conn)
            
            update_data = []
            for g, base in base_allocations.items():
                g_students = stud_df[stud_df['group_name'] == g]
                for offset, stud_id in enumerate(g_students['id'].tolist()):
                    update_data.append((base + offset, stud_id))
                    
            if update_data:
                c = conn.cursor()
                c.executemany("UPDATE students SET chest_number = ? WHERE id = ?", update_data)
                conn.commit()
                st.success("Chest numbers generated and saved!")
                st.rerun()
            else:
                st.info("No students found.")
            conn.close()

    # ------------------ PROGRAMS TAB ------------------
    with tab2:
        st.subheader(f"Add Event Programs ({current_mode} Mode)")
        
        p_types = ["Individual", "Group"]
        p_stage_types = ["On-stage", "Off-stage"]
        
        col3, col4 = st.columns(2)
        with col3:
            with st.expander("📝 Manual Entry", expanded=False):
                with st.form("program_form"):
                    p_name = st.text_input("Event Name (e.g. 100m Dash)")
                    p_type = st.selectbox("Event Type", p_types)
                    p_cat = st.selectbox("Category Eligibility", categories)
                    p_gender = st.selectbox("Gender Eligibility", genders + ["Mixed"])
                    
                    p_stage_type = None
                    # Only show stage type dropdown if it's Arts AND Individual.
                    if current_mode == 'Arts' and p_type == 'Individual':
                        p_stage_type = st.selectbox("Stage Type", p_stage_types)
                        
                    p_submitted = st.form_submit_button("Add Program")
                    
                    if p_submitted:
                        if p_name:
                            execute_query(
                                "INSERT INTO programs (name, type, category, gender, event_mode, stage_type) VALUES (?, ?, ?, ?, ?, ?)",
                                (p_name, p_type, p_cat, p_gender, current_mode, p_stage_type)
                            )
                            st.success(f"Added program: {p_name}")
                        else:
                            st.warning("Please enter a program name.")

        with col4:
            with st.expander("📄 Bulk Upload (Excel/CSV)", expanded=False):
                st.info("Your file should have columns: Name, Type, Category, Gender. For Arts Individual events, add a 'Stage Type' column (On-stage / Off-stage).")
                uploaded_program_file = st.file_uploader("Upload Program List", type=['xlsx', 'csv'], key='program_file')
                if uploaded_program_file is not None:
                    try:
                        if uploaded_program_file.name.endswith('.csv'):
                            df_p = pd.read_csv(uploaded_program_file)
                        else:
                            df_p = pd.read_excel(uploaded_program_file)
                        
                        df_p.columns = df_p.columns.str.lower().str.strip()
                        mapping_p = {'name': 'name', 'type': 'type', 'category': 'category', 'gender': 'gender', 'stage type': 'stage_type'}
                        df_p = df_p.rename(columns=mapping_p)
                        
                        df_p['event_mode'] = current_mode
                        
                        db_cols_p = ['name', 'type', 'category', 'gender', 'event_mode']
                        if 'stage_type' in df_p.columns:
                            db_cols_p.append('stage_type')
                            
                        df_p_tocreate = df_p[[c for c in db_cols_p if c in df_p.columns]]
                        
                        if st.button("Confirm & Upload Programs"):
                            conn = get_connection()
                            df_p_tocreate.to_sql('programs', conn, if_exists='append', index=False)
                            conn.close()
                            st.success(f"Successfully uploaded {len(df_p_tocreate)} programs!")
                            
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

        # Show current programs
        st.markdown("---")
        st.subheader(f"Current {current_mode} Programs")
        st.caption(f"Edit existing {current_mode} programs here:")
        df_programs = run_query("SELECT id, name, type, category, gender, stage_type FROM programs WHERE event_mode = ?", (current_mode,))
        edited_programs = st.data_editor(df_programs, hide_index=True, use_container_width=True, num_rows="dynamic", key="program_editor")
        if st.button("Save Changes to Programs", key="btn_save_programs"):
            conn = get_connection()
            conn.execute("DELETE FROM programs WHERE event_mode = ?", (current_mode,))
            conn.commit()
            df_to_save = edited_programs.copy()
            df_to_save['event_mode'] = current_mode
            df_to_save.to_sql("programs", conn, if_exists='append', index=False)
            conn.close()
            st.success(f"{current_mode} program database updated.")

    # ------------------ GROUP TEAMS TAB ------------------
    with tab3:
        st.subheader("Group Teams Management")
        
        with st.expander("📝 Manual Group Team Setup", expanded=False):
            st.markdown("Register your team members for group events manually under their respective House Group and Team Leader.")
            if not groups:
                st.warning("No House Groups found. Please configure them in Settings.")
            else:
                selected_house_group = st.selectbox("Select House Group", groups, key="grp_setup_house")
                st.markdown("---")
                
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    selected_cat_g = st.selectbox("Select Category", categories, key="grp_setup_cat")
                with col_g2:
                    selected_gen_g = st.selectbox("Select Gender", genders, key="grp_setup_gen")
                    
                if not selected_cat_g or not selected_gen_g:
                    st.warning("Please ensure categories and genders are set up in Settings.")
                else:
                    query_prog = "SELECT id, name FROM programs WHERE type = 'Group' AND category = ? AND gender = ? AND event_mode = ?"
                    df_prog_g = run_query(query_prog, (selected_cat_g, selected_gen_g, current_mode))
                    
                    if df_prog_g.empty:
                        st.info("No Group programs found for this Category and Gender in the current mode.")
                    else:
                        progs_g = df_prog_g.to_dict('records')
                        prog_options_g = {p['name']: p['id'] for p in progs_g}
                        
                        selected_prog_name_g = st.selectbox("Select Group Program", list(prog_options_g.keys()), key="grp_setup_prog")
                        selected_prog_id_g = prog_options_g[selected_prog_name_g]
                        
                        st.markdown("---")
                        st.subheader(f"Team Registration: {selected_house_group}")
                        
                        check_query = """
                            SELECT gp.leader_chest_number, gp.participant_name
                            FROM group_participants gp
                            JOIN students s ON gp.leader_chest_number = s.chest_number
                            WHERE gp.program_id = ? AND s.group_name = ?
                        """
                        df_existing = run_query(check_query, (selected_prog_id_g, selected_house_group))
                        
                        existing_leader_chest = None
                        existing_members = []
                        if not df_existing.empty:
                            existing_leader_chest = df_existing.iloc[0]['leader_chest_number']
                            existing_members = df_existing['participant_name'].tolist()
                            st.info(f"📌 A team is already configured for **{selected_house_group}**. You are in **Edit Mode**.")
                        else:
                            st.info(f"✨ No team configured for **{selected_house_group}** yet. You are in **Creation Mode**.")
                        
                        query_students_g = "SELECT chest_number, name FROM students WHERE category = ? AND group_name = ?"
                        params_students_g = [selected_cat_g, selected_house_group]
                        if selected_gen_g != "Mixed":
                            query_students_g += " AND gender = ?"
                            params_students_g.append(selected_gen_g)
                            
                        df_students_g = run_query(query_students_g, tuple(params_students_g))
                        
                        if df_students_g.empty:
                            st.warning(f"No students found in {selected_house_group} for this Category and Gender.")
                        else:
                            student_options_g = [f"{row['chest_number']} - {row['name']}" for _, row in df_students_g.iterrows()]
                            default_index = 0
                            if existing_leader_chest:
                                for idx, opt in enumerate(student_options_g):
                                    if opt.startswith(str(existing_leader_chest) + " -"):
                                        default_index = idx
                                        break
                                        
                            selected_student_str_g = st.selectbox("Select Team Leader (Chest Number - Name)", student_options_g, index=default_index, key="grp_setup_ldr")
                            
                            if selected_student_str_g:
                                leader_chest = int(selected_student_str_g.split(" - ")[0])
                                
                                with st.form("team_setup_form"):
                                    default_num_members = len(existing_members) if existing_members else 3
                                    num_members = st.number_input("Number of participants except group leader", min_value=1, max_value=50, value=default_num_members, step=1)
                                    st.write("Enter the names of the participants:")
                                    
                                    member_names = []
                                    for i in range(int(num_members)):
                                        default_val = existing_members[i] if i < len(existing_members) else ""
                                        name = st.text_input(f"Participant {i+1} Name", value=default_val, key=f"member_{i}_{selected_house_group}")
                                        member_names.append(name)
                                        
                                    btn_label = "Update Team Configuration" if existing_members else "Save Team Configuration"
                                    submit_g = st.form_submit_button(btn_label)
                                    
                                    if submit_g:
                                        if any(n.strip() == "" for n in member_names):
                                            st.warning("Please fill in all participant names before saving, or reduce the number of participants.")
                                        else:
                                            delete_q = "DELETE FROM group_participants WHERE program_id = ? AND leader_chest_number IN (SELECT chest_number FROM students WHERE group_name = ?)"
                                            execute_query(delete_q, (selected_prog_id_g, selected_house_group))
                                            for name_part in member_names:
                                                execute_query(
                                                    "INSERT INTO group_participants (program_id, leader_chest_number, participant_name) VALUES (?, ?, ?)",
                                                    (selected_prog_id_g, leader_chest, name_part.strip())
                                                )
                                            st.success("Team successfully registered!")
                                            st.rerun()
                                            
                        st.markdown("---")
                        st.subheader("Current Registered Teams for this Event")
                        query_teams_ex = """
                            SELECT s.group_name, gp.leader_chest_number, s.name as leader_name, gp.participant_name 
                            FROM group_participants gp
                            JOIN students s ON gp.leader_chest_number = s.chest_number
                            JOIN programs p ON gp.program_id = p.id
                            WHERE gp.program_id = ? AND p.event_mode = ?
                            ORDER BY s.group_name ASC, gp.leader_chest_number ASC
                        """
                        df_teams_ex = run_query(query_teams_ex, (selected_prog_id_g, current_mode))
                        
                        if df_teams_ex.empty:
                            st.info("No teams have been registered for this event yet.")
                        else:
                            teams_dict = {}
                            for _, row in df_teams_ex.iterrows():
                                leader_lbl = f"[{row['group_name']}] {row['leader_name']} (Chest: {row['leader_chest_number']})"
                                if leader_lbl not in teams_dict:
                                    teams_dict[leader_lbl] = {'chest': row['leader_chest_number'], 'members': []}
                                teams_dict[leader_lbl]['members'].append(row['participant_name'])
                                
                            for leader_lbl, data in teams_dict.items():
                                with st.expander(f"🏅 Team: {leader_lbl}"):
                                    for idx, member in enumerate(data['members']):
                                        st.write(f"{idx+1}. {member}")
                                    if st.button("Delete Team", key=f"del_{data['chest']}_{selected_prog_id_g}"):
                                        execute_query("DELETE FROM group_participants WHERE program_id = ? AND leader_chest_number = ?", 
                                                    (selected_prog_id_g, data['chest']))
                                        st.success("Team deleted!")
                                        st.rerun()

        with st.expander("📄 Bulk Upload Group Teams (Excel/CSV)", expanded=False):
            st.info("Your CSV should have EXACT Columns: GROUP, GENDER, CHEST NO:, PROGRAM LEADER NAME, NUMBER OF PARTICIPANTS, NAME OF PARTICIPANTS. (Multiple participant names should be separated by commas).")
        
        # We need Category, but it's not in their requested CSV columns. So we select it here:
        upload_cat = st.selectbox("Select Category for this CSV File (Since it's not in the CSV columns)", categories, key="bulk_upload_cat")
        
        uploaded_team_file = st.file_uploader("Upload Group Teams List", type=['xlsx', 'csv'], key='team_file')
        
        if uploaded_team_file is not None:
            try:
                if uploaded_team_file.name.endswith('.csv'):
                    df_t = pd.read_csv(uploaded_team_file)
                else:
                    df_t = pd.read_excel(uploaded_team_file)
                
                df_t.columns = df_t.columns.str.lower().str.strip()
                mapping_t = {
                    'group': 'name', 
                    'gender': 'gender',
                    'chest no:': 'leader_chest_number',
                    'chest no': 'leader_chest_number',
                    'name of participants': 'participant_name'
                }
                df_t = df_t.rename(columns=mapping_t)
                
                df_t['category'] = upload_cat
                
                required_cols = ['name', 'category', 'gender', 'leader_chest_number', 'participant_name']
                missing_cols = [c for c in required_cols if c not in df_t.columns]
                
                if missing_cols:
                    st.error(f"Missing required columns in your file: {', '.join(missing_cols)} (Ensure you have 'group', 'gender', 'chest no:', and 'name of participants')")
                else:
                    # Explode comma separated participants
                    df_t['participant_name'] = df_t['participant_name'].astype(str).str.split(',')
                    df_exploded = df_t.explode('participant_name')
                    df_exploded['participant_name'] = df_exploded['participant_name'].str.strip()
                    df_exploded = df_exploded[df_exploded['participant_name'] != ""]
                    
                    # Clean records
                    df_exploded['name'] = df_exploded['name'].astype(str).str.strip()
                    df_exploded['category'] = df_exploded['category'].astype(str).str.strip()
                    df_exploded['gender'] = df_exploded['gender'].astype(str).str.strip()
                    
                    df_db_progs = run_query("SELECT id as program_id, name, category, gender FROM programs WHERE type = 'Group' AND event_mode = ?", (current_mode,))
                    
                    # Merge to get program_id
                    df_merged = pd.merge(df_exploded, df_db_progs, on=['name', 'category', 'gender'], how='left')
                    
                    if df_merged['program_id'].isnull().any():
                        bad_rows = df_merged[df_merged['program_id'].isnull()]
                        st.error(f"Warning! {len(bad_rows)} names could not perfectly match an existing Group Program. Ensure 'GROUP'/Gender map exactly to an existing program in '{upload_cat}'.")
                        st.dataframe(bad_rows[['name', 'category', 'gender', 'leader_chest_number', 'participant_name']])
                    else:
                        st.success(f"Perfect match found! Extracted {len(df_merged)} individual participants. Ready to ingest.")
                        df_to_upload = df_merged[['program_id', 'leader_chest_number', 'participant_name']].copy()
                        
                        # Enforce datatypes
                        df_to_upload['leader_chest_number'] = pd.to_numeric(df_to_upload['leader_chest_number'], errors='coerce').fillna(0).astype(int)
                        
                        if st.button("Confirm & Upload Teams"):
                            conn = get_connection()
                            df_to_upload.to_sql('group_participants', conn, if_exists='append', index=False)
                            conn.close()
                            st.success(f"Successfully uploaded {len(df_to_upload)} individual participants!")
                            
            except Exception as e:
                st.error(f"Error processing file: {e}")
                
        # Current Group configurations
        st.markdown("---")
        st.subheader("Current Registered Participants Database")
        st.caption("You can delete or edit rows directly here and press save.")
        
        query_teams = """
            SELECT gp.program_id, p.name as program_name, p.category, p.gender, gp.leader_chest_number, gp.participant_name 
            FROM group_participants gp
            JOIN programs p ON gp.program_id = p.id
            WHERE p.event_mode = ?
        """
        df_group_parts = run_query(query_teams, (current_mode,))
        
        if df_group_parts.empty:
             st.info("No participants registered yet.")
        else:
            edited_groups = st.data_editor(df_group_parts, hide_index=True, use_container_width=True, num_rows="dynamic", key="group_editor")
            if st.button("Save Changes to Participants Database", key="btn_save_groups"):
                conn = get_connection()
                conn.execute("DELETE FROM group_participants WHERE program_id IN (SELECT id FROM programs WHERE event_mode = ?)", (current_mode,))
                conn.commit()
                # Extract only the DB columns
                df_to_save = edited_groups[['program_id', 'leader_chest_number', 'participant_name']]
                df_to_save.to_sql("group_participants", conn, if_exists='append', index=False)
                conn.close()
                st.success("Group participants database updated.")

    # ------------------ INDIVIDUAL ASSIGNATION TAB ------------------
    with tab4:
        st.subheader("Assign Individual Programs")
        st.markdown("Assign programs to individual students here.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_gen = st.selectbox("1. Gender", genders + ["Mixed"] if genders else [], key="ind_gen")
        with c2:
            sel_cat = st.selectbox("2. Category", categories, key="ind_cat")
        with c3:
            sel_grp = st.selectbox("3. Group", groups, key="ind_grp")
            
        if sel_gen and sel_cat and sel_grp:
            # Filter Students
            q_stud = "SELECT id, name, chest_number FROM students WHERE category=? AND group_name=?"
            params_stud = [sel_cat, sel_grp]
            if sel_gen != "Mixed":
                q_stud += " AND gender=?"
                params_stud.append(sel_gen)
                
            df_studs = run_query(q_stud, tuple(params_stud))
            
            # Filter Programs
            q_prog = "SELECT id, name FROM programs WHERE type='Individual' AND category=? AND event_mode=?"
            params_prog = [sel_cat, current_mode]
            if sel_gen != "Mixed":
                q_prog += " AND gender IN (?, 'Mixed')"
                params_prog.append(sel_gen)
            else:
                q_prog += " AND gender='Mixed'"
            
            df_progs = run_query(q_prog, tuple(params_prog))
            
            c4, c5 = st.columns(2)
            with c4:
                if not df_studs.empty:
                    df_studs['display_name'] = df_studs['name'] + " (Chest: " + df_studs['chest_number'].fillna(0).astype(int).astype(str) + ")"
                    stud_display = df_studs['display_name'].tolist()
                    sel_stud_names = st.multiselect("4. Student Name(s)", stud_display, key="ind_stud")
                else:
                    st.info("No students found.")
                    sel_stud_names = []
                    
            with c5:
                if not df_progs.empty:
                    prog_display = df_progs['name'].tolist()
                    sel_prog_name = st.selectbox("5. Program/Event", prog_display, key="ind_prog")
                    prog_idx = prog_display.index(sel_prog_name)
                    sel_prog_id = int(df_progs.iloc[prog_idx]['id'])
                else:
                    st.info("No individual programs found.")
                    sel_prog_id = None
                    
            if sel_stud_names and sel_prog_id:
                if st.button("➕ Assign Selected Program to Student(s)", type="primary"):
                    assigned_count = 0
                    already_assigned = 0
                    
                    for s_name in sel_stud_names:
                        stud_idx = stud_display.index(s_name)
                        sel_stud_id = int(df_studs.iloc[stud_idx]['id'])
                        
                        chk = run_query("SELECT id FROM individual_participants WHERE program_id=? AND student_id=?", (sel_prog_id, sel_stud_id))
                        if not chk.empty:
                            already_assigned += 1
                        else:
                            execute_query("INSERT INTO individual_participants (program_id, student_id) VALUES (?, ?)", (sel_prog_id, sel_stud_id))
                            assigned_count += 1
                            
                    if assigned_count > 0:
                        st.success(f"Successfully assigned {assigned_count} student(s) to the program!")
                    if already_assigned > 0:
                        st.warning(f"{already_assigned} student(s) were already assigned to this program and skipped.")
                    st.rerun()
                        
        st.markdown("---")
        st.subheader("Current Individual Assignations")
        st.caption("You can delete or edit rows directly here and press save.")
        
        q_assigns = """
            SELECT ip.program_id, ip.student_id, p.name as program_name, p.category, p.gender, s.name as student_name, s.group_name
            FROM individual_participants ip
            JOIN programs p ON ip.program_id = p.id
            JOIN students s ON ip.student_id = s.id
            WHERE p.event_mode = ?
        """
        try:
            df_assigns = run_query(q_assigns, (current_mode,))
            if df_assigns.empty:
                st.info("No individual assignations yet.")
            else:
                edited_assigns = st.data_editor(df_assigns, hide_index=True, use_container_width=True, num_rows="dynamic", key="assigns_editor")
                if st.button("Save Changes to Assignations", key="btn_save_assigns"):
                    conn = get_connection()
                    conn.execute("DELETE FROM individual_participants WHERE program_id IN (SELECT id FROM programs WHERE event_mode = ?)", (current_mode,))
                    conn.commit()
                    df_to_save = edited_assigns[['program_id', 'student_id']]
                    df_to_save = df_to_save.dropna()
                    df_to_save.to_sql("individual_participants", conn, if_exists='append', index=False)
                    conn.close()
                    st.success("Individual assignations updated.")
        except Exception as e:
            st.error(f"Error loading assignations: {e}")
