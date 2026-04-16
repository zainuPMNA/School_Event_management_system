import sqlite3
import random

DB_PATH = "sports_manager.db"

def generate_large_seed_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Clear existing data for a clean massive seed
    c.execute("DELETE FROM students")
    c.execute("DELETE FROM programs")
    c.execute("DELETE FROM group_participants")
    c.execute("DELETE FROM scores")

    # Dimensions
    categories = ['Kiddies', 'Sub-Junior', 'Junior', 'Senior', 'Super Senior']
    genders = ['Boys', 'Girls']
    groups = ['Group A', 'Group B', 'Group C']
    classes = ['5', '6', '7', '8', '9', '10', '11', '12']
    divisions = ['A', 'B', 'C', 'D']
    
    first_names_b = ["Liam", "Noah", "Oliver", "Elijah", "James", "William", "Benjamin", "Lucas", "Henry", "Theodore", "Zain", "Abid", "Sam", "Rahul", "Ali"]
    first_names_g = ["Olivia", "Emma", "Charlotte", "Amelia", "Ava", "Sophia", "Isabella", "Mia", "Evelyn", "Harper", "Riya", "Sara", "Fatima", "Aisha", "Chloe"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Khan", "Patel", "Ali", "Hassan", "Lee"]

    # 1. Generate 60 Students
    student_records = []
    chest_counter = 100
    boys = []
    girls = []

    for _ in range(30):
        # Boys
        name = f"{random.choice(first_names_b)} {random.choice(last_names)}"
        cls = random.choice(classes)
        div = random.choice(divisions)
        cat = random.choice(categories)
        grp = random.choice(groups)
        student_records.append((name, cls, div, "Boys", cat, grp, chest_counter))
        boys.append((name, chest_counter, grp, cat))
        chest_counter += 1

        # Girls
        name = f"{random.choice(first_names_g)} {random.choice(last_names)}"
        cls = random.choice(classes)
        div = random.choice(divisions)
        cat = random.choice(categories)
        grp = random.choice(groups)
        student_records.append((name, cls, div, "Girls", cat, grp, chest_counter))
        girls.append((name, chest_counter, grp, cat))
        chest_counter += 1

    c.executemany("""
        INSERT INTO students (name, class_name, division, gender, category, group_name, chest_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, student_records)

    # 2. Generate Programs
    programs = [
        # Track Events
        ("100m Sprint", "Individual"), ("200m Sprint", "Individual"),
        ("400m Run", "Individual"), ("800m Run", "Individual"),
        # Field Events
        ("Long Jump", "Individual"), ("High Jump", "Individual"),
        ("Shot Put", "Individual"), ("Javelin Throw", "Individual"),
        # Group Events
        ("4x100m Relay", "Group"), ("4x400m Relay", "Group"),
        ("Tug of War", "Group"), ("March Past", "Group")
    ]
    
    prog_inserts = []
    for p_name, p_type in programs:
        for cat in categories:
            for gen in genders:
                # Let's seed just some combos to avoid extreme bloat
                if random.random() > 0.3: # 70% chance to hold this event
                    prog_inserts.append((p_name, p_type, cat, gen))
            
            # also add mixed for group events
            if p_type == "Group" and random.random() > 0.5:
                prog_inserts.append((p_name, p_type, cat, "Mixed"))

    c.executemany("""
        INSERT INTO programs (name, type, category, gender)
        VALUES (?, ?, ?, ?)
    """, prog_inserts)
    
    c.execute("SELECT id, name, type, category, gender FROM programs")
    all_programs = c.fetchall()

    # 3. Simulate Scores and Group participation
    for prog in all_programs:
        p_id, p_name, p_type, p_cat, p_gen = prog
        
        # Determine eligible pool
        eligible = []
        if p_gen == "Boys": eligible = [b for b in boys if b[3] == p_cat]
        elif p_gen == "Girls": eligible = [g for g in girls if g[3] == p_cat]
        else: eligible = [x for x in boys + girls if x[3] == p_cat]
        
        if len(eligible) < 3:
            continue # not enough students to form top 3

        if p_type == "Individual":
            winners = random.sample(eligible, 3)
            pts = [(1, 5, 9.5), (2, 3, 10.1), (3, 1, 10.8)]
            for i in range(3):
                s_name, s_chest, s_grp, _ = winners[i]
                pos, assign_pt, mark = pts[i]
                c.execute("""
                    INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (p_id, f"{s_name} (Chest: {s_chest})", s_grp, pos, assign_pt, mark + random.random()))

        elif p_type == "Group":
            # Just pick 3 random group leaders from eligible representing their Houses
            leaders = random.sample(eligible, 3)
            pts = [(1, 10, 48.0), (2, 6, 49.5), (3, 2, 51.0)]
            
            for i in range(3):
                l_name, l_chest, l_grp, _ = leaders[i]
                pos, assign_pt, mark = pts[i]
                
                # Make dummy participants string
                other_participants = ", ".join([f"Participant_{x}" for x in range(3)])
                
                c.execute("""
                    INSERT INTO group_participants (program_id, leader_chest_number, participant_name)
                    VALUES (?, ?, ?)
                """, (p_id, l_chest, f"{l_name}, {other_participants}"))
                
                c.execute("""
                    INSERT INTO scores (program_id, student_or_group_leader, group_name, position, points_assigned, mark)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (p_id, f"{l_name} (Chest: {l_chest})", l_grp, pos, assign_pt, mark + random.random()))

    conn.commit()
    conn.close()
    print("Massive dataset successfully injected!")

if __name__ == "__main__":
    generate_large_seed_data()
