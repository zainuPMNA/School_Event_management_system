import streamlit as st
import pandas as pd
import os
from database import run_query, transaction, sync_rows
from views.ui import hero, require_admin, admin_password_set, check_admin_password, set_admin_password

# Which text columns elsewhere hold each lookup value, so renames can be applied everywhere
RENAME_TARGETS = {
    "categories": [("students", "category"), ("programs", "category")],
    "genders": [("students", "gender"), ("programs", "gender")],
    "groups": [("students", "group_name"), ("scores", "group_name")],
}


def save_lookup(table_name, original_df, edited_df):
    edited_df = edited_df.copy()
    edited_df['name'] = edited_df['name'].astype("string").str.strip()
    names = edited_df['name'].dropna()
    names = names[names != ""]
    if names.duplicated().any():
        st.error(f"Duplicate names: {', '.join(names[names.duplicated()].unique())}. Each entry must be unique.")
        return

    old_names = dict(zip(original_df['id'], original_df['name']))
    try:
        with transaction() as conn:
            for _, row in edited_df.dropna(subset=['id']).iterrows():
                old = old_names.get(int(row['id']))
                new = row['name']
                if old is not None and pd.notna(new) and new and new != old:
                    for tbl, col in RENAME_TARGETS.get(table_name, []):
                        conn.execute(f"UPDATE {tbl} SET {col} = ? WHERE {col} = ?", (new, old))
            edited_df = edited_df[edited_df['name'].notna() & (edited_df['name'] != "")]
            sync_rows(conn, table_name, original_df, edited_df, ["name"])
    except Exception as e:
        st.error(f"Nothing was saved because of an error: {e}")
        return

    deleted = set(original_df['name']) - set(edited_df['name'])
    for name in deleted:
        in_use = sum(
            int(run_query(f"SELECT COUNT(*) AS c FROM {tbl} WHERE {col} = ?", (name,)).iloc[0]['c'])
            for tbl, col in RENAME_TARGETS.get(table_name, [])
        )
        if in_use:
            st.warning(f"'{name}' was removed but is still used by {in_use} record(s). Update those records too.")
    st.toast(f"Saved {table_name}!", icon="✅")


def save_points(edited_df):
    df = edited_df.dropna(subset=['position', 'points']).copy()
    df['position'] = df['position'].astype(int)
    df['points'] = df['points'].astype(int)
    if df['position'].duplicated().any():
        st.error("Each position can only appear once.")
        return
    if (df['position'] < 1).any():
        st.error("Positions start at 1.")
        return
    with transaction() as conn:
        conn.execute("DELETE FROM points")
        conn.executemany("INSERT INTO points (position, points) VALUES (?, ?)", df[['position', 'points']].values.tolist())
    st.toast("Points saved! New scores will use these values.", icon="✅")


def lookup_tab(table_name, title, example, key):
    st.subheader(title)
    st.markdown(example)
    df = run_query(f"SELECT id, name FROM {table_name} ORDER BY id")
    edited = st.data_editor(df, num_rows="dynamic", hide_index=True, width="stretch", key=key,
                            column_config={"id": None, "name": st.column_config.TextColumn("Name", required=True)})
    if st.button(f"Save {title.replace('Manage ', '')}", key=f"save_{key}", type="primary"):
        save_lookup(table_name, df, edited)


def render():
    hero("Settings", "Categories, houses, genders, points, event details and security.", "⚙️")
    if not require_admin():
        return
    st.info("💡 **Tip**: Click a cell to edit it, or use the bottom row to add an entry. Renaming a value updates every student, program and score that uses it.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Categories", "Groups / Houses", "Genders", "Point Values", "Event Info", "🔐 Security"])

    with tab1:
        lookup_tab("categories", "Manage Categories", "e.g. Kiddies, Junior, Senior", "cat_editor")
    with tab2:
        lookup_tab("groups", "Manage Groups", "e.g. Group A, Blue House", "grp_editor")
    with tab3:
        lookup_tab("genders", "Manage Genders", "e.g. Boys, Girls", "gen_editor")

    with tab4:
        st.subheader("Manage Points")
        st.markdown("Points assigned for 1st, 2nd, 3rd, etc. Add rows for 4th, 5th… if you need them.")
        df_pts = run_query("SELECT position, points FROM points ORDER BY position")
        edited_pts = st.data_editor(df_pts, num_rows="dynamic", hide_index=True, width="stretch", key="pts_editor",
                                    column_config={"position": st.column_config.NumberColumn("Position", min_value=1, step=1),
                                                   "points": st.column_config.NumberColumn("Points", min_value=0, step=1)})
        if st.button("Save Points", type="primary"):
            save_points(edited_pts)

    with tab5:
        st.subheader("Event Information & Logo")
        st.markdown("Shown in the sidebar, on the live scoreboard, certificates and every downloaded document.")

        df_info = run_query("SELECT * FROM event_info LIMIT 1")
        cur = df_info.iloc[0] if not df_info.empty else {}
        get = lambda k: str(cur[k]) if len(df_info) and pd.notna(cur[k]) else ""

        with st.form("event_info_form"):
            school_name = st.text_input("School / Institution Name", value=get('school_name'))
            sports_name = st.text_input("Event Name (e.g. Annual Sports Meet)", value=get('sports_name'))
            year = st.text_input("Year", value=get('year'))
            logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])

            if st.form_submit_button("Save Event Info", type="primary"):
                logo_path = get('logo_path') or None
                if logo_file is not None:
                    os.makedirs("assets", exist_ok=True)
                    ext = logo_file.name.rsplit('.', 1)[-1].lower()
                    logo_path = f"assets/logo.{ext}"
                    with open(logo_path, "wb") as f:
                        f.write(logo_file.getbuffer())

                with transaction() as conn:
                    conn.execute("DELETE FROM event_info")
                    conn.execute("INSERT INTO event_info (school_name, sports_name, year, logo_path) VALUES (?, ?, ?, ?)",
                                 (school_name, sports_name, year, logo_path))
                st.toast("Event information saved!", icon="✅")
                st.rerun()

        logo_path = get('logo_path')
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, width=220, caption="Current logo")

    with tab6:
        st.subheader("Admin Password")
        st.markdown("When a password is set, only logged-in admins can enter scores, edit data, change settings or "
                    "restore backups. Dashboards, the live scoreboard, certificates and downloads stay open to everyone.")
        has_pwd = admin_password_set()
        st.markdown(f"**Status:** {'🔐 Password protection is ON' if has_pwd else '🔓 No password — anyone can edit'}")

        with st.form("pwd_form", clear_on_submit=True):
            current = st.text_input("Current password", type="password") if has_pwd else ""
            new = st.text_input("New password (min 4 characters)", type="password")
            confirm = st.text_input("Confirm new password", type="password")
            c1, c2 = st.columns(2)
            save = c1.form_submit_button("Set password", type="primary")
            remove = c2.form_submit_button("Remove password") if has_pwd else False

            if save or remove:
                if has_pwd and not check_admin_password(current):
                    st.error("Current password is incorrect.")
                elif remove:
                    set_admin_password(None)
                    st.success("Password removed. Anyone can edit now.")
                elif len(new) < 4:
                    st.error("Password must be at least 4 characters.")
                elif new != confirm:
                    st.error("Passwords do not match.")
                else:
                    set_admin_password(new)
                    st.session_state["is_admin"] = True
                    st.success("Password set! Keep it safe — you'll need it to edit data.")
