import streamlit as st
import pandas as pd
import plotly.express as px
from database import run_query
from views.downloads import generate_docx
from views.ui import hero, stat_cards, podium

PALETTE = ["#6C5CE7", "#00B894", "#E17055", "#0984E3", "#FDCB6E", "#E84393", "#00CEC9", "#636E72"]


def _style(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Poppins, sans-serif"), margin=dict(t=50, l=10, r=10, b=10),
        legend_title_text="",
    )
    return fig


def _export_buttons(df, title, file_stub, key):
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'),
                           f'{file_stub}.csv', 'text/csv', key=f"{key}_csv")
    with col_b:
        st.download_button("📝 Download Word File (.docx)", generate_docx(df, title), f'{file_stub}.docx',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document', key=f"{key}_docx")


def render():
    current_mode = st.session_state.get('event_mode', 'Sports')
    hero(f"{current_mode} Analytics Dashboard", f"Live view of the {current_mode} event standings.", "📊")

    summary = run_query("""
        SELECT
          (SELECT COUNT(*) FROM programs WHERE event_mode = ?) AS programs,
          (SELECT COUNT(DISTINCT program_id) FROM scores WHERE program_id IN (SELECT id FROM programs WHERE event_mode = ?)) AS done,
          (SELECT COUNT(*) FROM students) AS students,
          (SELECT COALESCE(SUM(points_assigned), 0) FROM scores WHERE program_id IN (SELECT id FROM programs WHERE event_mode = ?)) AS pts
    """, (current_mode, current_mode, current_mode)).iloc[0]
    stat_cards([
        ("🎯", f"{int(summary['done'])}/{int(summary['programs'])}", "Programs completed"),
        ("🧑‍🎓", int(summary['students']), "Students registered"),
        ("⭐", int(summary['pts']), "Points awarded"),
        ("⏳", int(summary['programs']) - int(summary['done']), "Programs pending"),
    ])

    tab1, tab2, tab3 = st.tabs(["🏆 Group Leaderboard", "📂 Category-wise", "🏅 Individual Champions"])

    # ------------------ GROUP LEADERBOARD ------------------
    with tab1:
        df_group = run_query("""
            SELECT s.group_name, SUM(s.points_assigned) as total_points
            FROM scores s
            JOIN programs p ON s.program_id = p.id
            WHERE p.event_mode = ? AND s.group_name IS NOT NULL
            GROUP BY s.group_name
            ORDER BY total_points DESC
        """, (current_mode,))

        if not df_group.empty and df_group['total_points'].sum() > 0:
            podium([(r['group_name'], int(r['total_points'])) for _, r in df_group.iterrows()])

            col1, col2 = st.columns([2, 1])
            with col1:
                fig_bar = px.bar(df_group, x='group_name', y='total_points', title="Total Points by Group",
                                 text='total_points', color='group_name', color_discrete_sequence=PALETTE)
                fig_bar.update_traces(textposition='outside', marker_line_width=0)
                fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Points")
                st.plotly_chart(_style(fig_bar), width="stretch")
            with col2:
                fig_pie = px.pie(df_group, names='group_name', values='total_points', title="Point Distribution",
                                 hole=0.55, color_discrete_sequence=PALETTE)
                st.plotly_chart(_style(fig_pie), width="stretch")

            st.dataframe(df_group.rename(columns={'group_name': 'Group', 'total_points': 'Total Points'}),
                         width="stretch", hide_index=True)
            st.markdown("### Export")
            _export_buttons(df_group, "Overall Group Standings", "group_standings", "grp")
        else:
            st.info("No scores logged yet. Standings will appear here as soon as results are saved. 🏁")

    # ------------------ CATEGORY-WISE ------------------
    with tab2:
        df_cat = run_query("""
            SELECT p.category, s.group_name, SUM(s.points_assigned) AS points
            FROM scores s JOIN programs p ON p.id = s.program_id
            WHERE p.event_mode = ? AND s.group_name IS NOT NULL
            GROUP BY p.category, s.group_name
        """, (current_mode,))
        if df_cat.empty:
            st.info("No scores logged yet.")
        else:
            fig = px.bar(df_cat, x='category', y='points', color='group_name', barmode='group', text='points',
                         title="House points per category", color_discrete_sequence=PALETTE)
            fig.update_layout(xaxis_title="", yaxis_title="Points")
            st.plotly_chart(_style(fig), width="stretch")
            pivot = df_cat.pivot_table(index='category', columns='group_name', values='points', fill_value=0, aggfunc='sum')
            pivot['🏆 Leader'] = pivot.idxmax(axis=1)
            st.dataframe(pivot, width="stretch")

    # ------------------ INDIVIDUAL CHAMPIONS ------------------
    with tab3:
        st.subheader("Individual Top Scorers")
        df_indiv = run_query("""
            SELECT st.chest_number, st.name, st.class_name, st.gender, st.category, st.group_name,
                   SUM(sc.points_assigned) AS total_points,
                   SUM(CASE WHEN sc.position = 1 THEN 1 ELSE 0 END) AS golds
            FROM scores sc
            JOIN programs p ON sc.program_id = p.id
            JOIN students st ON st.id = sc.student_id
            WHERE p.type = 'Individual' AND p.event_mode = ?
            GROUP BY st.id
            HAVING total_points > 0
            ORDER BY total_points DESC, golds DESC
        """, (current_mode,))

        if not df_indiv.empty:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                sel_gender = st.selectbox("Filter by Gender", ["All"] + df_indiv['gender'].dropna().unique().tolist())
            with col_f2:
                sel_cat = st.selectbox("Filter by Category", ["All"] + df_indiv['category'].dropna().unique().tolist())

            filtered_df = df_indiv.copy()
            if sel_gender != "All":
                filtered_df = filtered_df[filtered_df['gender'] == sel_gender]
            if sel_cat != "All":
                filtered_df = filtered_df[filtered_df['category'] == sel_cat]

            if not filtered_df.empty:
                max_pts = filtered_df['total_points'].max()
                champions = filtered_df[filtered_df['total_points'] == max_pts]
                names = ", ".join(champions['name'].astype(str))
                st.success(f"🏆 Champion{'s' if len(champions) > 1 else ''}: **{names}** with {int(max_pts)} points")
                podium([(f"{r['name']} ({r['group_name']})", int(r['total_points'])) for _, r in filtered_df.head(3).iterrows()])

                st.markdown("**Full List (Filtered)**")
                st.dataframe(filtered_df, width="stretch", hide_index=True)
                st.markdown("### Export")
                _export_buttons(filtered_df, "Individual Top Scorers", "individual_standings", "ind")
            else:
                st.info("No participants match these filters.")
        else:
            st.info("No individual scores logged yet.")
