import sqlite3
import random

DB_PATH = "sports_manager.db"

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Add some students
    students = [
        ("John Doe", "10A", "Boys", "Senior", "Group A", 101),
        ("Mike Smith", "10B", "Boys", "Senior", "Group B", 102),
        ("Alice Cooper", "10C", "Girls", "Senior", "Group A", 103),
        ("Emma Watson", "10D", "Girls", "Senior", "Group B", 104),
        ("Bob Johnson", "9A", "Boys", "Junior", "Group C", 105),
        ("Sarah Williams", "9B", "Girls", "Junior", "Group C", 106)
    ]
    
    for s in students:
        c.execute("""
            INSERT INTO students (name, class_name, gender, category, group_name, chest_number)
            VALUES (?, ?, ?, ?, ?, ?)
        """, s)

    # 2. Add Programs
    programs = [
        ("100m Sprint", "Individual", "Senior", "Boys"),
        ("200m Sprint", "Individual", "Senior", "Girls"),
        ("Long Jump", "Individual", "Junior", "Boys"),
        ("4x100m Relay", "Group", "Senior", "Mixed")
    ]
    
    prog_ids = []
    for p in programs:
        c.execute("""
            INSERT INTO programs (name, type, category, gender)
            VALUES (?, ?, ?, ?)
        """, p)
        prog_ids.append(c.lastrowid)

    # 3. Add Group Participants for Relay (prog_ids[3])
    # Group A Team (Leader: John Doe)
    c.execute("""
        INSERT INTO group_participants (program_id, leader_chest_number, participant_name)
        VALUES (?, ?, ?)
    """, (prog_ids[3], 101, "John Doe, Alice Cooper, David, Tom"))
    
    # Group B Team (Leader: Mike Smith)
    c.execute("""
        INSERT INTO group_participants (program_id, leader_chest_number, participant_name)
        VALUES (?, ?, ?)
    """, (prog_ids[3], 102, "Mike Smith, Emma Watson, Lily, James"))

    # 4. Add Scores / Win results
    
    # INDIVIDUAL: 100m Sprint Senior Boys
    # 1st place: John Doe, 2nd place: Mike Smith
    c.execute("""
        INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (prog_ids[0], "John Doe (Chest: 101)", "Group A", 1, 5, 11.5))
    
    c.execute("""
        INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (prog_ids[0], "Mike Smith (Chest: 102)", "Group B", 2, 3, 12.1))
    
    # GROUP: 4x100m Relay Senior Mixed
    # 1st place: Mike Smith's team (Group B), 2nd place: John Doe's team (Group A)
    c.execute("""
        INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (prog_ids[3], "Mike Smith (Chest: 102)", "Group B", 1, 5, 45.2))
    
    c.execute("""
        INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (prog_ids[3], "John Doe (Chest: 101)", "Group A", 2, 3, 46.8))

    conn.commit()
    conn.close()
    print("Database successfully seeded with dummy testing data!")

if __name__ == "__main__":
    seed_data()
