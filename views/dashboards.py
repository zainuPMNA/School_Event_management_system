import streamlit as st
import pandas as pd
import plotly.express as px
from database import run_query

def render():
    current_mode = st.session_state.get('event_mode', 'Sports')
    st.title(f"📊 {current_mode} Analytics Dashboard")
    st.markdown(f"Live view of the {current_mode} event standings.")

    tab1, tab2 = st.tabs(["🏆 Group Leaderboard", "🏅 Individual Champions"])

    # ------------------ GROUP LEADERBOARD ------------------
    with tab1:
        st.subheader("Overall Group Standings")
        
        # Query total points per group
        df_group = run_query("""
            SELECT s.group_name, SUM(s.points_assigned) as total_points 
            FROM scores s
            JOIN programs p ON s.program_id = p.id
            WHERE p.event_mode = ?
            GROUP BY s.group_name
            ORDER BY total_points DESC
        """, (current_mode,))
        
        if not df_group.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Interactive Bar Chart
                fig_bar = px.bar(
                    df_group, 
                    x='group_name', y='total_points', 
                    title="Total Points by Group",
                    text='total_points',
                    color='group_name',
                    template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
                )
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                # Interactive Pie Chart
                fig_pie = px.pie(
                    df_group, 
                    names='group_name', values='total_points', 
                    title="Point Distribution",
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
            # Raw Data Table
            st.dataframe(df_group, use_container_width=True)
            
            # Export Buttons
            from views.downloads import generate_docx
            st.markdown("### Export")
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    label="📥 Download CSV",
                    data=df_group.to_csv(index=False).encode('utf-8'),
                    file_name='group_standings.csv',
                    mime='text/csv',
                    key="grp_csv"
                )
            with col_b:
                st.download_button(
                    label="📝 Download Word File (.docx)",
                    data=generate_docx(df_group, "Overall Group Standings"),
                    file_name='group_standings.docx',
                    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    key="grp_docx"
                )
            
        else:
            st.info("No scores logged yet.")

    # ------------------ INDIVIDUAL CHAMPIONS ------------------
    with tab2:
        st.subheader("Individual Top Scorers")
        
        # We need to map scores to students.
        # Ensure we only calculate Individual events.
        query = """
            SELECT 
                st.name, 
                st.class_name, 
                st.gender, 
                st.category, 
                st.group_name,
                SUM(sc.points_assigned) as total_points
            FROM scores sc
            JOIN programs p ON sc.program_id = p.id
            JOIN students st ON sc.student_or_group_leader LIKE st.name || '%' AND sc.group_name = st.group_name
            WHERE p.type = 'Individual' AND p.event_mode = ?
            GROUP BY st.name, st.class_name, st.gender, st.category, st.group_name
            ORDER BY total_points DESC
        """
        try:
            df_indiv = run_query(query, (current_mode,))
        except Exception as e:
            df_indiv = pd.DataFrame()
            
        if not df_indiv.empty:
            # Filters
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                genders = ["All"] + df_indiv['gender'].dropna().unique().tolist()
                sel_gender = st.selectbox("Filter by Gender", genders)
            with col_f2:
                categories = ["All"] + df_indiv['category'].dropna().unique().tolist()
                sel_cat = st.selectbox("Filter by Category", categories)
                
            # Apply Filters
            filtered_df = df_indiv.copy()
            if sel_gender != "All":
                filtered_df = filtered_df[filtered_df['gender'] == sel_gender]
            if sel_cat != "All":
                filtered_df = filtered_df[filtered_df['category'] == sel_cat]
                
            if not filtered_df.empty:
                # Find maximum points in the filtered dataset
                max_pts = filtered_df['total_points'].max()
                # Determine the absolute champions for this filter
                champions = filtered_df[filtered_df['total_points'] == max_pts]
                
                st.success(f"🏆 Max Points in this category: {max_pts}")
                st.markdown("### 🥇 Champions Board")
                st.dataframe(champions, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("**Full List (Filtered)**")
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                
                # Export Buttons
                from views.downloads import generate_docx
                st.markdown("### Export")
                col_c, col_d = st.columns(2)
                with col_c:
                    st.download_button(
                        label="📥 Download CSV",
                        data=filtered_df.to_csv(index=False).encode('utf-8'),
                        file_name='individual_standings.csv',
                        mime='text/csv',
                        key="ind_csv"
                    )
                with col_d:
                    st.download_button(
                        label="📝 Download Word File (.docx)",
                        data=generate_docx(filtered_df, "Individual Top Scorers"),
                        file_name='individual_standings.docx',
                        mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        key="ind_docx"
                    )
            else:
                st.info("No participants match these filters.")
                
        else:
            st.info("No individual scores logged yet, or unable to map scores to students.")
