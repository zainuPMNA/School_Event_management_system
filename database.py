import sqlite3
import pandas as pd
import os

DB_PATH = "sports_manager.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Settings Tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )""")
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS genders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )""")
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )""")
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS points (
        position INTEGER PRIMARY KEY,
        points INTEGER NOT NULL
    )""")
    
    # Main Tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        class_name TEXT,
        gender TEXT,
        category TEXT,
        group_name TEXT,
        chest_number INTEGER
    )""")
    
    try:
        c.execute("ALTER TABLE students ADD COLUMN chest_number INTEGER")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE students ADD COLUMN division TEXT")
    except sqlite3.OperationalError:
        pass
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS programs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Individual' or 'Group'
        category TEXT,
        gender TEXT,
        event_mode TEXT DEFAULT 'Sports',
        stage_type TEXT
    )""")
    
    try:
        c.execute("ALTER TABLE programs ADD COLUMN event_mode TEXT DEFAULT 'Sports'")
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE programs ADD COLUMN stage_type TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute("ALTER TABLE programs ADD COLUMN date TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE programs ADD COLUMN time TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE programs ADD COLUMN venue TEXT")
    except sqlite3.OperationalError:
        pass
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER,
        student_or_group_leader TEXT,
        group_name TEXT,
        position INTEGER,
        points_assigned INTEGER,
        mark REAL,
        FOREIGN KEY(program_id) REFERENCES programs(id)
    )""")
    
    try:
        c.execute("ALTER TABLE scores ADD COLUMN mark REAL")
    except sqlite3.OperationalError:
        pass
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS group_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER,
        leader_chest_number INTEGER,
        participant_name TEXT,
        FOREIGN KEY(program_id) REFERENCES programs(id)
    )""")
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS event_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school_name TEXT,
        sports_name TEXT,
        year TEXT,
        logo_path TEXT
    )""")
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS individual_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER,
        student_id INTEGER,
        FOREIGN KEY(program_id) REFERENCES programs(id),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    
    # Seed default values if empty
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        defaults_cat = [('Kiddies',), ('Sub-Junior',), ('Junior',), ('Senior',), ('Super Senior',)]
        c.executemany("INSERT INTO categories (name) VALUES (?)", defaults_cat)
        
    c.execute("SELECT COUNT(*) FROM genders")
    if c.fetchone()[0] == 0:
        defaults_gen = [('Boys',), ('Girls',)]
        c.executemany("INSERT INTO genders (name) VALUES (?)", defaults_gen)
        
    c.execute("SELECT COUNT(*) FROM groups")
    if c.fetchone()[0] == 0:
        defaults_grp = [('Group A',), ('Group B',), ('Group C',)]
        c.executemany("INSERT INTO groups (name) VALUES (?)", defaults_grp)
        
    c.execute("SELECT COUNT(*) FROM points")
    if c.fetchone()[0] == 0:
        defaults_pts = [(1, 5), (2, 3), (3, 1)]
        c.executemany("INSERT INTO points (position, points) VALUES (?, ?)", defaults_pts)
        
    conn.commit()
    conn.close()

# --- Helper DB functions ---

def run_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def get_table_data(table_name):
    return run_query(f"SELECT * FROM {table_name}")

def bulk_insert(table_name, df):
    conn = get_connection()
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()
