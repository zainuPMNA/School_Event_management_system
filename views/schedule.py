import streamlit as st
import pandas as pd
from database import get_connection, run_query
import io
from docx import Document

import os
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def generate_schedule_docx(df):
    doc = Document()
    
    # Fetch event info
    try:
        df_info = run_query("SELECT * FROM event_info LIMIT 1")
    except Exception:
        df_info = pd.DataFrame()
        
    school_name = "Tournament"
    sports_name = "Annual Sports Day"
    year = ""
    logo_path = None
    
    if not df_info.empty:
        school_name = df_info['school_name'].iloc[0] if pd.notna(df_info['school_name'].iloc[0]) else school_name
        sports_name = df_info['sports_name'].iloc[0] if pd.notna(df_info['sports_name'].iloc[0]) else sports_name
        year = df_info['year'].iloc[0] if pd.notna(df_info['year'].iloc[0]) else year
        logo_path = df_info['logo_path'].iloc[0] if pd.notna(df_info['logo_path'].iloc[0]) else None

    # Header section
    header_para = doc.add_paragraph()
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    if logo_path and os.path.exists(logo_path):
        run = header_para.add_run()
        run.add_picture(logo_path, width=Inches(1.0))
        header_para.add_run("\n")
        
    run = header_para.add_run(f"{school_name}\n")
    run.font.size = Pt(16)
    run.bold = True
    
    if year:
        run = header_para.add_run(f"{sports_name} - {year}\n")
    else:
        run = header_para.add_run(f"{sports_name}\n")
    run.font.size = Pt(12)
    
    header_para.add_run("\n")
    run = header_para.add_run("Event Time Schedule")
    run.font.size = Pt(14)
    run.bold = True
    
    # Add a table for data
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'
    
    hdr_cells = table.rows[0].cells
    for i, col_name in enumerate(df.columns):
        hdr_cells[i].text = str(col_name)
    
    for index, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, val in enumerate(row):
            row_cells[i].text = str(val) if pd.notna(val) else ""
            
    # Add Footer with signatures
    doc.add_paragraph("\n\n\n")
    
    sig_table = doc.add_table(rows=1, cols=3)
    sig_table.autofit = True
    
    cell_left = sig_table.cell(0, 0)
    cell_left.text = "________________________\nSports Chairman"
    cell_left.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    cell_center = sig_table.cell(0, 1)
    cell_center.text = "________________________\nSports Coordinator"
    cell_center.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_right = sig_table.cell(0, 2)
    cell_right.text = "________________________\nPrincipal"
    cell_right.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def render():
    current_mode = st.session_state.get('event_mode', 'Sports')
    st.title(f"🗓️ {current_mode} Event Schedule Planner")
    st.markdown("Set the **Date**, **Time**, and **Venue** for all your programs. Once configured, you can generate and download a final Time Schedule document.")
    
    st.subheader("Manage Program Schedule")
    st.caption("Edit the Date, Time, and Venue columns directly in the table below, then click Save.")
    
    try:
        df_prog = run_query("SELECT id, name, category, type, date, time, venue FROM programs WHERE event_mode = ? ORDER BY date ASC, time ASC", (current_mode,))
    except Exception as e:
        df_prog = pd.DataFrame()
        st.error(f"Database error: {e}")
        
    if df_prog.empty:
        st.info("No programs found. Please add programs in 'Upload & Manage Data' first.")
        return
        
    # Let user edit date, time, venue
    edited_prog = st.data_editor(
        df_prog,
        hide_index=True,
        use_container_width=True,
        disabled=["id", "name", "category", "type"],
        key="schedule_editor"
    )
    
    if st.button("💾 Save Schedule Settings"):
        conn = get_connection()
        c = conn.cursor()
        for _, row in edited_prog.iterrows():
            c.execute(
                "UPDATE programs SET date = ?, time = ?, venue = ? WHERE id = ?",
                (row['date'], row['time'], row['venue'], row['id'])
            )
        conn.commit()
        conn.close()
        st.success("Schedule settings saved successfully!")
    
    st.markdown("---")
    st.subheader("Generate Final Schedule")
    
    # Reload from DB for the view to ensure we have the saved data
    view_df = run_query("SELECT date as Date, time as Time, venue as Venue, category as Category, name as Program, type as Type FROM programs WHERE event_mode = ? ORDER BY date ASC, time ASC, venue ASC", (current_mode,))
    
    st.dataframe(view_df, use_container_width=True, hide_index=True)
    
    col1, col2 = st.columns(2)
    csv = view_df.to_csv(index=False).encode('utf-8')
    docx_bytes = generate_schedule_docx(view_df)
    
    with col1:
        st.download_button(
            label="📥 Download Schedule as CSV",
            data=csv,
            file_name="Event_Schedule.csv",
            mime='text/csv',
            key="dl_sched_csv"
        )
    with col2:
        st.download_button(
            label="📝 Download Schedule as Word File",
            data=docx_bytes,
            file_name="Event_Schedule.docx",
            mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            key="dl_sched_docx"
        )
