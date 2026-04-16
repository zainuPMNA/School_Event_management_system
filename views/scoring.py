import streamlit as st
import pandas as pd
from database import get_connection, run_query, execute_query

def render():
    st.title("🏆 Enter & Manage Scores")
    st.markdown("Record match results here. Filter the event, type the position directly into the table, and hit save!")

    # Fetch lookup
    try:
        df_cat = run_query("SELECT name FROM categories")
        df_gen = run_query("SELECT name FROM genders")
        categories = df_cat['name'].tolist() if not df_cat.empty else []
        genders = df_gen['name'].tolist() if not df_gen.empty else []
    except Exception:
        categories, genders = [], []
        
    st.subheader("Log a New Score")
    current_mode = st.session_state.get('event_mode', 'Sports')
    
    with st.container(border=True):
        st.markdown("**1. Filter Program**")
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_gen = st.selectbox("Gender", genders + ["Mixed"] if genders else [])
        with c2:
            sel_cat = st.selectbox("Category", categories)
        with c3:
            sel_type = st.selectbox("Type", ["Individual", "Group"])
            
        stage_type_filter = "All"
        if current_mode == 'Arts' and sel_type == 'Individual':
            stage_type_filter = st.selectbox("Stage Type", ["All", "On-stage", "Off-stage"])
            
        if not sel_gen or not sel_cat:
            st.warning("Ensure categories and genders exist in Settings.")
            return
            
        # Fetch matching programs
        query = "SELECT id, name FROM programs WHERE category=? AND gender=? AND type=? AND event_mode=?"
        params = [sel_cat, sel_gen, sel_type, current_mode]
        
        if current_mode == 'Arts' and sel_type == 'Individual' and stage_type_filter != "All":
            query += " AND stage_type=?"
            params.append(stage_type_filter)
            
        df_prog = run_query(query, tuple(params))
        
        if df_prog.empty:
            st.info("No programs found matching these filters in the current mode.")
        else:
            prog_display = [f"{r['name']}" for _, r in df_prog.iterrows()]
            selected_prog_str = st.selectbox("Select Program", prog_display)
            
            # Get prog id
            prog_idx = prog_display.index(selected_prog_str)
            prog_id = df_prog.iloc[prog_idx]['id']
            
            st.markdown(f"**2. Enter Marks for: {selected_prog_str}**")
            # Prepare Dataframe
            if sel_type == "Individual":
                try:
                    count_assigned = run_query("SELECT COUNT(*) as c FROM individual_participants WHERE program_id=?", (prog_id,)).iloc[0]['c']
                except Exception:
                    count_assigned = 0
                
                if count_assigned > 0:
                    q_part = """
                        SELECT s.chest_number, s.name, s.group_name 
                        FROM individual_participants ip
                        JOIN students s ON ip.student_id = s.id
                        WHERE ip.program_id = ?
                    """
                    df_part = run_query(q_part, (prog_id,))
                    if df_part.empty:
                        st.info("No assigned students found for this program.")
                    else:
                        df_part.rename(columns={'chest_number': 'Chest Number', 'name': 'Participant Name', 'group_name': 'Group'}, inplace=True)
                else:
                    df_part = pd.DataFrame()
                    st.warning("⚠️ No students have been assigned to this Individual program yet. Please assign them in 'Upload & Manage Data -> Individual Assignation'.")
            else:
                q_part = """
                    SELECT gp.leader_chest_number, s.name, s.group_name 
                    FROM group_participants gp
                    JOIN students s ON gp.leader_chest_number = s.chest_number
                    WHERE gp.program_id = ?
                """
                df_part = run_query(q_part, (prog_id,))
                if df_part.empty:
                    st.info("No registered teams found for this group event. Add them in Group Team Setup.")
                else:
                    df_part.rename(columns={'leader_chest_number': 'Chest Number', 'name': 'Program Leader Name', 'group_name': 'Group'}, inplace=True)
                
            if not df_part.empty:
                event_mode = st.session_state.get('event_mode', 'Sports')
                
                # Fetch default points for lookup 
                df_pts = run_query("SELECT position, points FROM points")
                pts_dict = dict(zip(df_pts['position'], df_pts['points'])) if not df_pts.empty else {}
                
                if event_mode == 'Sports':
                    st.info("SPORTS MODE: Select '1', '2', or '3' for the winners. Unselected participants will safely receive 0 points.")
                    
                    df_existing = run_query("SELECT student_or_group_leader, position FROM scores WHERE program_id = ?", (prog_id,))
                    
                    if sel_type == "Individual":
                        df_part['full_name'] = df_part['Participant Name'].astype(str) + " (Chest: " + df_part['Chest Number'].astype(str) + ")"
                    else:
                        df_part['full_name'] = df_part['Program Leader Name'].astype(str) + " (Chest: " + df_part['Chest Number'].astype(str) + ")"
                    
                    if not df_existing.empty:
                        mapping_pos = dict(zip(df_existing['student_or_group_leader'], df_existing['position']))
                        df_part['Position'] = df_part['full_name'].map(mapping_pos).fillna(0).astype(int).astype(str).replace('0', None)
                    else:
                        df_part['Position'] = None
                        
                    df_part.drop(columns=['full_name'], inplace=True)

                    columns_config = {
                        "Chest Number": st.column_config.NumberColumn("Chest Number", disabled=True, format="%d"),
                        "Participant Name": st.column_config.TextColumn("Participant Name", disabled=True),
                        "Program Leader Name": st.column_config.TextColumn("Program Leader Name", disabled=True),
                        "Group": st.column_config.TextColumn("House Group", disabled=True),
                        "Position": st.column_config.SelectboxColumn("Position", options=["1", "2", "3"])
                    }
                    
                    edited_df = st.data_editor(
                        df_part, 
                        column_config=columns_config,
                        hide_index=True, 
                        use_container_width=True, 
                        key=f"editor_{prog_id}"
                    )
                    
                    if st.button("💾 Save Assigned Places", type="primary"):
                        df_to_save = edited_df.copy()
                        df_to_save['Position'] = df_to_save['Position'].fillna(0).astype(int)
                        
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM scores WHERE program_id = ?", (int(prog_id),))
                        
                        inserted = 0
                        for _, row in df_to_save.iterrows():
                            pos = row['Position']
                            pts = pts_dict.get(pos, 0) if pos in [1, 2, 3] else 0
                            mark_val = 0.0 # Sports mode does not use mark
                            grp = row['Group']
                            
                            student_or_leader = row['Participant Name'] if sel_type == "Individual" else row['Program Leader Name']
                            leader_chest = row['Chest Number']
                            full_ident = f"{student_or_leader} (Chest: {int(leader_chest)})" if pd.notna(leader_chest) else student_or_leader
                            
                            try:
                                c.execute("INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark) VALUES (?, ?, ?, ?, ?, ?)", (int(prog_id), full_ident, grp, pos, pts, mark_val))
                            except Exception:
                                c.execute("INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned) VALUES (?, ?, ?, ?, ?)", (int(prog_id), full_ident, grp, pos, pts))
                            inserted += 1
                        
                        conn.commit()
                        conn.close()
                        st.success(f"Successfully tracked placements for {inserted} records!")
                        st.rerun()

                else: # Arts Mode
                    st.info("ARTS MODE: The system will auto-rank based on your marks. Provide any position points (e.g. 4th, 5th) globally in Settings!")
                    win_condition = st.radio("Win Condition (Auto-Ranking)", ["Highest Mark Wins", "Lowest Mark Wins"], horizontal=True)
                    
                    df_existing = run_query("SELECT student_or_group_leader, mark FROM scores WHERE program_id = ?", (prog_id,))
                    
                    if sel_type == "Individual":
                        df_part['full_name'] = df_part['Participant Name'].astype(str) + " (Chest: " + df_part['Chest Number'].astype(str) + ")"
                    else:
                        df_part['full_name'] = df_part['Program Leader Name'].astype(str) + " (Chest: " + df_part['Chest Number'].astype(str) + ")"
                    
                    if not df_existing.empty:
                        mapping_marks = dict(zip(df_existing['student_or_group_leader'], df_existing['mark']))
                        df_part['Mark'] = df_part['full_name'].map(mapping_marks)
                    else:
                        df_part['Mark'] = None
                        
                    df_part.drop(columns=['full_name'], inplace=True)

                    columns_config = {
                        "Chest Number": st.column_config.NumberColumn("Chest Number", disabled=True, format="%d"),
                        "Participant Name": st.column_config.TextColumn("Participant Name", disabled=True),
                        "Program Leader Name": st.column_config.TextColumn("Program Leader Name", disabled=True),
                        "Group": st.column_config.TextColumn("House Group", disabled=True),
                        "Mark": st.column_config.NumberColumn("Mark (Type Score here)", min_value=0.0, step=0.01)
                    }
                    
                    edited_df = st.data_editor(
                        df_part, 
                        column_config=columns_config,
                        hide_index=True, 
                        use_container_width=True, 
                        key=f"editor_{prog_id}"
                    )
                    
                    if st.button("💾 Calculate & Save Scores", type="primary"):
                        df_to_save = edited_df.copy()
                        df_to_save['Mark'] = df_to_save['Mark'].fillna(0.0)
                        df_ranked = df_to_save[df_to_save['Mark'] > 0].copy()
                        
                        if not df_ranked.empty:
                            is_ascend = True if "Lowest" in win_condition else False
                            df_ranked['Position'] = df_ranked['Mark'].rank(method='min', ascending=is_ascend).astype(int)
                            
                            df_to_save = pd.merge(df_to_save, df_ranked[['Chest Number', 'Position']], on='Chest Number', how='left')
                            df_to_save['Position'] = df_to_save['Position'].fillna(0).astype(int)
                        else:
                            df_to_save['Position'] = 0
                            
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM scores WHERE program_id = ?", (int(prog_id),))
                        
                        inserted = 0
                        for _, row in df_to_save.iterrows():
                            mark_val = float(row['Mark'])
                            pos = int(row['Position'])
                            # UNBOUNDED POINTS FOR ARTS:
                            pts = pts_dict.get(pos, 0)
                            grp = row['Group']
                            
                            student_or_leader = row['Participant Name'] if sel_type == "Individual" else row['Program Leader Name']
                            leader_chest = row['Chest Number']
                            full_ident = f"{student_or_leader} (Chest: {int(leader_chest)})" if pd.notna(leader_chest) else student_or_leader
                            
                            try:
                                c.execute("INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark) VALUES (?, ?, ?, ?, ?, ?)", (int(prog_id), full_ident, grp, pos, pts, mark_val))
                            except Exception:
                                c.execute("INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned) VALUES (?, ?, ?, ?, ?)", (int(prog_id), full_ident, grp, pos, pts))
                            inserted += 1
                            
                        conn.commit()
                        conn.close()
                        st.success(f"Successfully calculated rankings and saved {inserted} records!")
                        st.rerun()

    # ------------------ HISTORY TABLE ------------------
    st.markdown("---")
    st.subheader("Score Logs (History)")
    st.markdown("To fix a typo, simply select the Program above, correct the inputs, and press Save again to instantly recalculate.")
    
    query = """
    SELECT 
        s.id as score_id, 
        p.name as program_name,
        p.category as category,
        p.type as event_type,
        s.student_or_group_leader as participant, 
        s.group_name, 
        COALESCE(s.mark, 0) as mark,
        s.position, 
        s.points_assigned 
    FROM scores s
    JOIN programs p ON s.program_id = p.id
    WHERE p.event_mode = ?
    ORDER BY s.id DESC
    """
    
    try:
        df_scores = run_query(query, (current_mode,))
    except Exception: # Fallback if mark doesn't exist
        df_scores = run_query(query.replace("COALESCE(s.mark, 0) as mark,", ""), (current_mode,))

    if not df_scores.empty:
        # Auto format numeric positions to string representations
        def format_pos(x):
            if x == 1: return "1st"
            if x == 2: return "2nd"
            if x == 3: return "3rd"
            if int(x) > 3: return f"{int(x)}th"
            return ""
            
        df_scores['Rank'] = df_scores['position'].apply(format_pos)
        
        display_cols = ['program_name', 'category', 'event_type', 'participant', 'group_name']
        
        # Only show marks logically if we recorded them!
        if 'mark' in df_scores.columns and current_mode == 'Arts':
            display_cols.append('mark')
            
        display_cols.extend(['Rank', 'points_assigned'])
        
        df_display = df_scores[display_cols].rename(columns={
            'program_name': 'Program',
            'category': 'Category',
            'event_type': 'Type',
            'participant': 'Participant',
            'group_name': 'House Group',
            'mark': 'Recorded Mark',
            'points_assigned': 'Points'
        })
        
        st.dataframe(df_display, hide_index=True, use_container_width=True)
    else:
        st.info("No scores have been logged yet.")
