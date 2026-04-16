import sqlite3
import random

DB_PATH = "sports_manager.db"

def reset_and_seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Total Wipe
    tables = [
        "students", "programs", "group_participants", "scores",
        "categories", "genders", "groups", "points", "event_info"
    ]
    for t in tables:
        c.execute(f"DELETE FROM {t}")
        
    print("Database wiped clean.")

    # 2. SETTINGS ARRANGEMENT
    # Event Info
    c.execute("""
        INSERT INTO event_info (school_name, sports_name, year)
        VALUES ('Global Excellence Academy', 'Annual Arts & Sports Fest', '2026')
    """)

    # Categories
    categories = ['LP (Lower Primary)', 'UP (Upper Primary)', 'HS (High School)', 'HSS (Higher Secondary)']
    c.executemany("INSERT INTO categories (name) VALUES (?)", [(cat,) for cat in categories])

    # Divisions & Classes
    class_map = {
        'LP (Lower Primary)': ['1', '2', '3', '4'],
        'UP (Upper Primary)': ['5', '6', '7'],
        'HS (High School)': ['8', '9', '10'],
        'HSS (Higher Secondary)': ['11', '12']
    }
    divisions = ['A', 'B', 'C']

    # Genders
    genders = ['Boys', 'Girls']
    c.executemany("INSERT INTO genders (name) VALUES (?)", [(g,) for g in genders])

    # Groups (Houses)
    houses = ['Red House', 'Blue House', 'Green House', 'Yellow House']
    c.executemany("INSERT INTO groups (name) VALUES (?)", [(h,) for h in houses])

    # Points Array (EXTENDED Array for Arts auto-scoring mapping)
    points_array = [
        (1, 10), # 1st = 10 pts
        (2, 8),  # 2nd = 8 pts
        (3, 6),  # 3rd = 6 pts
        (4, 4),  # 4th = 4 pts
        (5, 2)   # 5th = 2 pts
    ]
    c.executemany("INSERT INTO points (position, points) VALUES (?, ?)", points_array)

    print("Settings arranged.")

    # 3. STUDENTS SEEDING
    first_names_b = ["Aarav", "Vihaan", "Aditya", "Rohan", "Arjun", "Leo", "Lucas", "Oliver", "Noah", "Elijah", "Tariq", "Zain", "Farhan"]
    first_names_g = ["Diya", "Aisha", "Ananya", "Riya", "Priya", "Mia", "Ava", "Sophia", "Amelia", "Isabella", "Fatima", "Zara", "Sana"]
    last_names = ["Sharma", "Patel", "Khan", "Singh", "Das", "Smith", "Johnson", "Williams", "Brown", "Jones"]

    chest_counter = 1000
    student_records = []
    
    # Store fast lookup
    student_pool_b = []
    student_pool_g = []

    # Distribute 100 students logically
    for _ in range(50):
        # Boy
        cat_b = random.choice(categories)
        s_name_b = f"{random.choice(first_names_b)} {random.choice(last_names)}"
        student_records.append((s_name_b, random.choice(class_map[cat_b]), random.choice(divisions), 'Boys', cat_b, random.choice(houses), chest_counter))
        student_pool_b.append((s_name_b, chest_counter, student_records[-1][5], cat_b))
        chest_counter += 1

        # Girl
        cat_g = random.choice(categories)
        s_name_g = f"{random.choice(first_names_g)} {random.choice(last_names)}"
        student_records.append((s_name_g, random.choice(class_map[cat_g]), random.choice(divisions), 'Girls', cat_g, random.choice(houses), chest_counter))
        student_pool_g.append((s_name_g, chest_counter, student_records[-1][5], cat_g))
        chest_counter += 1

    c.executemany("""
        INSERT INTO students (name, class_name, division, gender, category, group_name, chest_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, student_records)

    print("Students flooded.")

    # 4. PROGRAMS SEEDING (Arts & Sports)
    programs = [
        # Indiv Sports
        ("100m Sprint", "Individual"), ("Long Jump", "Individual"), ("Shot Put", "Individual"),
        # Group Sports
        ("4x100m Relay", "Group"), ("Tug of War", "Group"), 
        # Indiv Arts
        ("Elocution (English)", "Individual"), ("Light Music", "Individual"), ("Pencil Drawing", "Individual"),
        # Group Arts
        ("Group Dance", "Group"), ("Patriotic Song", "Group")
    ]

    prog_list = []
    p_id = 1
    for p_name, p_type in programs:
        # Assign to 3 random categories
        for cat in random.sample(categories, 3):
            if p_type == "Individual":
                for gen in ['Boys', 'Girls']:
                    # 50% chance they have this event
                    if random.random() > 0.5:
                        prog_list.append((p_id, p_name, p_type, cat, gen))
                        p_id += 1
            else:
                # Group events usually Mixed or single gender
                gen = random.choice(['Boys', 'Girls', 'Mixed'])
                prog_list.append((p_id, p_name, p_type, cat, gen))
                p_id += 1

    c.executemany("""
        INSERT INTO programs (id, name, type, category, gender)
        VALUES (?, ?, ?, ?, ?)
    """, prog_list)

    print("Programs established.")

    # 5. SCORE INJECTION & GROUP TEAM ASSIGNMENTS
    for p in prog_list:
        pid, pname, ptype, pcat, pgen = p
        
        elig = []
        if pgen == 'Boys': elig = [s for s in student_pool_b if s[3] == pcat]
        elif pgen == 'Girls': elig = [s for s in student_pool_g if s[3] == pcat]
        else: elig = [s for s in student_pool_b + student_pool_g if s[3] == pcat]
        
        # We need at least 5 to give 1-5 pos
        if len(elig) < 5:
            continue
            
        pts = {1:10, 2:8, 3:6, 4:4, 5:2}
        
        if ptype == "Individual":
            competitors = random.sample(elig, 5)
            # Assign Positions 1 to 5 and Marks
            base_mark = 90.0
            for pos in range(1, 6):
                s_name, s_chest, s_grp, _ = competitors[pos-1]
                m = base_mark - (pos * random.uniform(1.5, 4.0)) # descending mark
                c.execute("""
                    INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pid, f"{s_name} (Chest: {s_chest})", s_grp, pos, pts[pos], round(m, 2)))
                
        elif ptype == "Group":
            # Leaders representing 5 independent houses? We only have 4 houses. 
            # So let's pick 3 random houses for Group
            leaders = random.sample(elig, 3) 
            base_mark = 95.0
            
            for pos in range(1, 4): # only 1st, 2nd, 3rd
                l_name, l_chest, l_grp, _ = leaders[pos-1]
                m = base_mark - (pos * random.uniform(2.0, 5.0))
                
                parts = ", ".join([f"Partic_{x}" for x in range(3)])
                c.execute("""
                    INSERT INTO group_participants (program_id, leader_chest_number, participant_name)
                    VALUES (?, ?, ?)
                """, (pid, l_chest, f"{l_name}, {parts}"))
                
                c.execute("""
                    INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pid, f"{l_name} (Chest: {l_chest})", l_grp, pos, pts[pos], round(m, 2)))

    conn.commit()
    conn.close()
    print("Scores mathematically layered for testing!")

if __name__ == "__main__":
    reset_and_seed()
