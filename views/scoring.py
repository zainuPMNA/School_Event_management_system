from datetime import datetime

import streamlit as st
import pandas as pd
from database import run_query, transaction
from views.ui import hero, require_admin


def _ordinal(n):
    n = int(n)
    if n <= 0:
        return ""
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _save_scores(prog_id, rows):
    """rows: list of dicts with student_id, chest, label, group, position, points, mark. Atomic replace."""
    now = datetime.now().isoformat(timespec="seconds")
    with transaction() as conn:
        conn.execute("DELETE FROM scores WHERE program_id = ?", (prog_id,))
        conn.executemany(
            """INSERT INTO scores (program_id, student_id, chest_number, student_or_group_leader, group_name,
                                   position, points_assigned, mark, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(prog_id, r['student_id'], r['chest'], r['label'], r['group'], r['position'],
              r['points'], r['mark'], now) for r in rows],
        )


def render():
    current_mode = st.session_state.get('event_mode', 'Sports')
    hero("Enter & Manage Scores", "Pick a program, enter places or marks, and save — leaderboards update instantly.", "🏆")
    if not require_admin():
        return

    # Fetch lookup
    try:
        categories = run_query("SELECT name FROM categories")['name'].tolist()
        genders = run_query("SELECT name FROM genders")['name'].tolist()
    except Exception:
        categories, genders = [], []

    df_pts = run_query("SELECT position, points FROM points ORDER BY position")
    pts_dict = {int(p): int(v) for p, v in zip(df_pts['position'], df_pts['points'])} if not df_pts.empty else {}

    st.subheader("Log a New Score")

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

        query = """SELECT p.id, p.name, COALESCE(p.win_condition, 'Highest') AS win_condition,
                          (SELECT COUNT(*) FROM scores s WHERE s.program_id = p.id) AS n_scores
                   FROM programs p WHERE category=? AND gender=? AND type=? AND event_mode=?"""
        params = [sel_cat, sel_gen, sel_type, current_mode]
        if current_mode == 'Arts' and sel_type == 'Individual' and stage_type_filter != "All":
            query += " AND stage_type=?"
            params.append(stage_type_filter)
        df_prog = run_query(query + " ORDER BY p.name", tuple(params))

        if df_prog.empty:
            st.info("No programs found matching these filters in the current mode.")
        else:
            labels = [f"{'✅' if r['n_scores'] else '⏳'} {r['name']}" for _, r in df_prog.iterrows()]
            prog_idx = st.selectbox("Select Program (✅ = scored, ⏳ = pending)", range(len(labels)), format_func=lambda i: labels[i])
            prog = df_prog.iloc[prog_idx]
            prog_id = int(prog['id'])
            selected_prog_str = prog['name']

            st.markdown(f"**2. Enter results for: {selected_prog_str}**")
            name_col = "Participant Name" if sel_type == "Individual" else "Program Leader Name"
            if sel_type == "Individual":
                df_part = run_query("""
                    SELECT s.id AS student_id, s.chest_number, s.name, s.group_name
                    FROM individual_participants ip
                    JOIN students s ON ip.student_id = s.id
                    WHERE ip.program_id = ?
                    ORDER BY s.chest_number
                """, (prog_id,))
                if df_part.empty:
                    st.warning("⚠️ No students have been assigned to this Individual program yet. Please assign them in 'Upload & Manage Data -> Individual Assignation'.")
            else:
                df_part = run_query("""
                    SELECT MIN(s.id) AS student_id, gp.leader_chest_number AS chest_number, s.name, s.group_name
                    FROM group_participants gp
                    JOIN students s ON gp.leader_chest_number = s.chest_number
                    WHERE gp.program_id = ?
                    GROUP BY gp.leader_chest_number, s.name, s.group_name
                    ORDER BY gp.leader_chest_number
                """, (prog_id,))
                if df_part.empty:
                    st.info("No registered teams found for this group event. Add them in Group Team Setup.")

            if not df_part.empty:
                df_part = df_part.rename(columns={'chest_number': 'Chest Number', 'name': name_col, 'group_name': 'Group'})
                df_existing = run_query("SELECT student_id, chest_number, position, mark FROM scores WHERE program_id = ?", (prog_id,))
                by_student = {int(r['student_id']): r for _, r in df_existing.iterrows() if pd.notna(r['student_id'])}

                base_cfg = {
                    "student_id": None,  # hidden
                    "Chest Number": st.column_config.NumberColumn("Chest Number", disabled=True, format="%d"),
                    name_col: st.column_config.TextColumn(name_col, disabled=True),
                    "Group": st.column_config.TextColumn("House Group", disabled=True),
                }

                def build_rows(df_to_save, positions, marks=None):
                    rows = []
                    for i, row in df_to_save.iterrows():
                        pos = int(positions[i]) if pd.notna(positions[i]) else 0
                        chest = int(row['Chest Number']) if pd.notna(row['Chest Number']) else None
                        name = row[name_col]
                        rows.append({
                            'student_id': int(row['student_id']) if pd.notna(row['student_id']) else None,
                            'chest': chest,
                            'label': f"{name} (Chest: {chest})" if chest is not None else name,
                            'group': row['Group'],
                            'position': pos,
                            'points': pts_dict.get(pos, 0) if pos > 0 else 0,
                            'mark': float(marks[i]) if marks is not None and pd.notna(marks[i]) else None,
                        })
                    return rows

                if current_mode == 'Sports':
                    max_pos = max([3, len(df_part)] + list(pts_dict.keys()))
                    pos_options = [str(i) for i in range(1, max_pos + 1)]
                    st.info("SPORTS MODE: choose a place for each finisher. Leave blank for no place (0 points). "
                            f"Points per place come from Settings: {', '.join(f'{_ordinal(k)}={v}' for k, v in pts_dict.items())}.")

                    df_part['Position'] = [
                        str(int(by_student[int(sid)]['position']))
                        if int(sid) in by_student and pd.notna(by_student[int(sid)]['position']) and by_student[int(sid)]['position'] > 0
                        else None
                        for sid in df_part['student_id']
                    ]
                    cfg = dict(base_cfg, Position=st.column_config.SelectboxColumn("Position", options=pos_options))
                    edited_df = st.data_editor(df_part, column_config=cfg, hide_index=True, width="stretch", key=f"editor_{prog_id}")

                    chosen = pd.to_numeric(edited_df['Position'], errors='coerce')
                    dupes = chosen[chosen.notna() & chosen.duplicated(keep=False)].unique()
                    if len(dupes):
                        st.warning(f"⚠️ More than one participant has place {', '.join(_ordinal(d) for d in sorted(dupes))}. "
                                   "That's fine for a tie — otherwise please correct it before saving.")

                    if st.button("💾 Save Assigned Places", type="primary"):
                        rows = build_rows(edited_df, chosen)
                        _save_scores(prog_id, rows)
                        winners = [r for r in rows if r['position'] == 1]
                        st.session_state['score_flash'] = f"Saved results for {selected_prog_str}! " + (
                            f"🥇 {winners[0]['label']}" if winners else "")
                        st.rerun()

                else:  # Arts Mode
                    st.info("ARTS MODE: type each participant's mark. The system ranks them automatically. "
                            "Leave the mark **blank** for anyone absent — a mark of 0 still counts.")
                    win_condition = st.radio(
                        "Win Condition (Auto-Ranking) — saved for this program",
                        ["Highest Mark Wins", "Lowest Mark Wins"], horizontal=True,
                        index=1 if prog['win_condition'] == 'Lowest' else 0, key=f"win_{prog_id}",
                    )
                    df_part['Mark'] = [
                        by_student[int(sid)]['mark'] if int(sid) in by_student else None for sid in df_part['student_id']
                    ]
                    df_part['Mark'] = pd.to_numeric(df_part['Mark'], errors='coerce')
                    cfg = dict(base_cfg, Mark=st.column_config.NumberColumn("Mark (Type Score here)", min_value=0.0, step=0.01))
                    edited_df = st.data_editor(df_part, column_config=cfg, hide_index=True, width="stretch", key=f"editor_{prog_id}")

                    if st.button("💾 Calculate & Save Scores", type="primary"):
                        marks = pd.to_numeric(edited_df['Mark'], errors='coerce')
                        is_ascend = "Lowest" in win_condition
                        positions = marks.rank(method='min', ascending=is_ascend)
                        rows = build_rows(edited_df, positions, marks)
                        _save_scores(prog_id, rows)
                        with transaction() as conn:
                            conn.execute("UPDATE programs SET win_condition = ? WHERE id = ?",
                                         ('Lowest' if is_ascend else 'Highest', prog_id))
                        winners = sorted([r for r in rows if r['position'] > 0], key=lambda r: r['position'])
                        st.session_state['score_flash'] = f"Ranked and saved {selected_prog_str}! " + (
                            f"🥇 {winners[0]['label']}" if winners else "")
                        st.rerun()

    if st.session_state.get('score_flash'):
        st.success(st.session_state.pop('score_flash'))
        st.balloons()

    # ------------------ HISTORY TABLE ------------------
    st.markdown("---")
    st.subheader("Score Logs (History)")
    st.markdown("To fix a typo, select the Program above, correct the inputs, and press Save again — it recalculates instantly.")

    df_scores = run_query("""
        SELECT p.name AS program_name, p.category, p.type AS event_type,
               COALESCE(st.name || ' (Chest: ' || s.chest_number || ')', s.student_or_group_leader) AS participant,
               s.group_name, s.mark, s.position, s.points_assigned, s.updated_at
        FROM scores s
        JOIN programs p ON s.program_id = p.id
        LEFT JOIN students st ON st.id = s.student_id
        WHERE p.event_mode = ?
        ORDER BY s.updated_at DESC, s.id DESC
    """, (current_mode,))

    if not df_scores.empty:
        df_scores['Rank'] = df_scores['position'].fillna(0).apply(_ordinal)
        display_cols = ['program_name', 'category', 'event_type', 'participant', 'group_name']
        if current_mode == 'Arts':
            display_cols.append('mark')
        display_cols.extend(['Rank', 'points_assigned', 'updated_at'])

        df_display = df_scores[display_cols].rename(columns={
            'program_name': 'Program',
            'category': 'Category',
            'event_type': 'Type',
            'participant': 'Participant',
            'group_name': 'House Group',
            'mark': 'Recorded Mark',
            'points_assigned': 'Points',
            'updated_at': 'Saved At',
        })
        st.dataframe(df_display, hide_index=True, width="stretch")
    else:
        st.info("No scores have been logged yet.")
