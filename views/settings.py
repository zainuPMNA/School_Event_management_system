import streamlit as st
import pandas as pd
import os
from database import get_connection, run_query

def save_table(table_name, df, is_points=False):
    conn = get_connection()
    c = conn.cursor()
    
    # Delete existing rows
    c.execute(f"DELETE FROM {table_name}")
    conn.commit()
    
    # Drop rows with NaN (in case user added dynamic row but left it blank)
    if not is_points:
        df = df.dropna(subset=['name'])
    else:
        df = df.dropna(subset=['position', 'points'])
    
    # Insert back
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()
    
    st.success(f"Changes to {table_name} saved successfully!")

def render():
    st.title("⚙️ Settings")
    st.markdown("Use the tables below to add, edit, or remove the core settings for the sports event.")
    st.info("💡 **Tip**: You can directly click on cells to edit the text, or click the bottom row of a table to add a new entry. Press the 'Save' button below each table to apply changes.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Categories", "Groups / Houses", "Genders", "Point Values", "Event Info"])

    with tab1:
        st.subheader("Manage Categories")
        st.markdown("e.g. Kiddies, Junior, Senior")
        df_cat = run_query("SELECT id, name FROM categories")
        # Allow dynamic rows
        edited_cat = st.data_editor(df_cat, num_rows="dynamic", hide_index=True, use_container_width=True, key="cat_editor")
        if st.button("Save Categories"):
            save_table("categories", edited_cat)

    with tab2:
        st.subheader("Manage Groups")
        st.markdown("e.g. Group A, Blue House")
        df_grp = run_query("SELECT id, name FROM groups")
        edited_grp = st.data_editor(df_grp, num_rows="dynamic", hide_index=True, use_container_width=True, key="grp_editor")
        if st.button("Save Groups"):
            save_table("groups", edited_grp)

    with tab3:
        st.subheader("Manage Genders")
        df_gen = run_query("SELECT id, name FROM genders")
        edited_gen = st.data_editor(df_gen, num_rows="dynamic", hide_index=True, use_container_width=True, key="gen_editor")
        if st.button("Save Genders"):
            save_table("genders", edited_gen)

    with tab4:
        st.subheader("Manage Points")
        st.markdown("Points assigned for 1st, 2nd, 3rd, etc.")
        df_pts = run_query("SELECT position, points FROM points")
        # Points table should allow adding more positions (4th, 5th) if needed
        edited_pts = st.data_editor(df_pts, num_rows="dynamic", hide_index=True, use_container_width=True, key="pts_editor")
        if st.button("Save Points"):
            save_table("points", edited_pts, is_points=True)

    with tab5:
        st.subheader("Event Information & Logo")
        st.markdown("Set your school details and logos to be displayed on downloaded documents.")
        
        try:
            df_info = run_query("SELECT * FROM event_info LIMIT 1")
        except Exception:
            df_info = pd.DataFrame()
            
        cur_school = df_info['school_name'].iloc[0] if not df_info.empty and pd.notna(df_info['school_name'].iloc[0]) else ""
        cur_sports = df_info['sports_name'].iloc[0] if not df_info.empty and pd.notna(df_info['sports_name'].iloc[0]) else ""
        cur_year = str(df_info['year'].iloc[0]) if not df_info.empty and pd.notna(df_info['year'].iloc[0]) else ""
        
        with st.form("event_info_form"):
            school_name = st.text_input("School / Institution Name", value=cur_school)
            sports_name = st.text_input("Annual Sports Name", value=cur_sports)
            year = st.text_input("Year", value=cur_year)
            logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])
            
            if st.form_submit_button("Save Event Info"):
                logo_path = df_info['logo_path'].iloc[0] if not df_info.empty else None
                
                if logo_file is not None:
                    if not os.path.exists("assets"):
                        os.makedirs("assets")
                    
                    # save logo
                    ext = logo_file.name.split('.')[-1]
                    logo_path = f"assets/logo.{ext}"
                    with open(logo_path, "wb") as f:
                        f.write(logo_file.getbuffer())
                
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM event_info")
                c.execute(
                    "INSERT INTO event_info (school_name, sports_name, year, logo_path) VALUES (?, ?, ?, ?)",
                    (school_name, sports_name, year, logo_path)
                )
                conn.commit()
                conn.close()
                st.success("Event Information saved successfully!")
