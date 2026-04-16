import sqlite3
import pandas as pd

conn = sqlite3.connect("sports_manager.db")

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
    WHERE p.type = 'Individual'
    GROUP BY st.name, st.class_name, st.gender, st.category, st.group_name
    ORDER BY total_points DESC
"""

df = pd.read_sql_query(query, conn)
print(df)
conn.close()
