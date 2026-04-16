import sqlite3
import random

DB_PATH = "sports_manager.db"

def inject_random_schedules():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, name, type FROM programs")
    programs = c.fetchall()

    dates = ['2026-04-20', '2026-04-21', '2026-04-22']
    times = ['09:00 AM', '09:30 AM', '10:00 AM', '10:45 AM', '11:15 AM', '01:00 PM', '02:30 PM', '03:45 PM', '04:15 PM']
    venues_sports = ['Main Ground Track', 'Field Area', 'Indoor Court', 'Central Ground']
    venues_arts = ['Auditorium A', 'Main Stage', 'Seminar Hall', 'Open Theatre']

    update_records = []
    
    for p in programs:
        p_id, p_name, p_type = p
        
        assigned_date = random.choice(dates)
        assigned_time = random.choice(times)
        
        # Super rough heuristic to assign venue based on event name
        if any(x in p_name.lower() for x in ['sprint', 'jump', 'throw', 'relay', 'war', 'past']):
            assigned_venue = random.choice(venues_sports)
        else:
            assigned_venue = random.choice(venues_arts)
            
        update_records.append((assigned_date, assigned_time, assigned_venue, p_id))

    c.executemany("""
        UPDATE programs 
        SET date = ?, time = ?, venue = ?
        WHERE id = ?
    """, update_records)

    conn.commit()
    conn.close()
    print(f"Successfully appended completely random schedules across {len(programs)} unique events!")

if __name__ == "__main__":
    inject_random_schedules()
