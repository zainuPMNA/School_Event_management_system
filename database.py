import os
import re
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import pandas as pd

DB_PATH = "sports_manager.db"
BACKUP_DIR = "backups"


def get_connection():
    # timeout lets several judges save at the same time without "database is locked" errors
    return sqlite3.connect(DB_PATH, timeout=15)


@contextmanager
def transaction():
    """Yield a connection; commit if the block succeeds, roll back everything if it fails."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _add_column(c, table, column_def):
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
    except sqlite3.OperationalError:
        pass


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

    c.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
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
    _add_column(c, "students", "chest_number INTEGER")
    _add_column(c, "students", "division TEXT")

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
    _add_column(c, "programs", "event_mode TEXT DEFAULT 'Sports'")
    _add_column(c, "programs", "stage_type TEXT")
    _add_column(c, "programs", "date TEXT")
    _add_column(c, "programs", "time TEXT")
    _add_column(c, "programs", "venue TEXT")
    _add_column(c, "programs", "win_condition TEXT DEFAULT 'Highest'")

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
    _add_column(c, "scores", "mark REAL")
    _add_column(c, "scores", "student_id INTEGER")
    _add_column(c, "scores", "chest_number INTEGER")
    _add_column(c, "scores", "updated_at TEXT")

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

    _backfill_score_links(c)

    conn.commit()
    conn.close()


def _backfill_score_links(c):
    """Older versions stored the participant only as text like 'Name (Chest: 105)'.
    Link those rows to the real student so leaderboards no longer depend on name matching."""
    rows = c.execute(
        "SELECT id, student_or_group_leader FROM scores WHERE chest_number IS NULL"
    ).fetchall()
    for score_id, label in rows:
        m = re.search(r'\(Chest:\s*(\d+)\)', str(label))
        if m:
            c.execute("UPDATE scores SET chest_number = ? WHERE id = ?", (int(m.group(1)), score_id))
    c.execute("""
        UPDATE scores SET student_id = (
            SELECT s.id FROM students s WHERE s.chest_number = scores.chest_number LIMIT 1
        )
        WHERE student_id IS NULL AND chest_number IS NOT NULL
    """)


# --- Helper DB functions ---

def run_query(query, params=()):
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def execute_query(query, params=()):
    with transaction() as conn:
        conn.execute(query, params)


def get_table_data(table_name):
    return run_query(f"SELECT * FROM {table_name}")


def bulk_insert(table_name, df):
    with transaction() as conn:
        df.to_sql(table_name, conn, if_exists='append', index=False)


def _clean(val):
    """Convert pandas/numpy values into plain Python values SQLite understands."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(val, "item"):
        return val.item()
    return val


def sync_rows(conn, table, original_df, edited_df, columns, scope_sql="", scope_params=(), fixed=None):
    """Apply edits from a st.data_editor table without wiping columns the editor doesn't show.

    Rows keep their id, so links from other tables (scores, participants) stay intact.
    Returns the list of ids that were deleted so callers can clean up linked rows.
    """
    fixed = fixed or {}
    original_ids = set(int(i) for i in original_df['id'].dropna()) if 'id' in original_df else set()
    edited_ids = set()

    for _, row in edited_df.iterrows():
        values = [_clean(row.get(col)) for col in columns]
        row_id = _clean(row.get('id'))
        if row_id is not None and int(row_id) in original_ids:
            row_id = int(row_id)
            edited_ids.add(row_id)
            set_sql = ", ".join(f"{col} = ?" for col in columns)
            conn.execute(f"UPDATE {table} SET {set_sql} WHERE id = ?", values + [row_id])
        else:
            if all(v is None or (isinstance(v, str) and not v.strip()) for v in values):
                continue  # blank row added in the editor
            cols = columns + list(fixed.keys())
            vals = values + list(fixed.values())
            placeholders = ", ".join("?" for _ in cols)
            conn.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})", vals)

    deleted = sorted(original_ids - edited_ids)
    for row_id in deleted:
        conn.execute(f"DELETE FROM {table} WHERE id = ? {scope_sql}", (row_id, *scope_params))
    return deleted


def cleanup_orphans(conn):
    """Remove assignments and scores that point to students/programs which no longer exist."""
    conn.execute("DELETE FROM individual_participants WHERE program_id NOT IN (SELECT id FROM programs)")
    conn.execute("DELETE FROM individual_participants WHERE student_id NOT IN (SELECT id FROM students)")
    conn.execute("DELETE FROM group_participants WHERE program_id NOT IN (SELECT id FROM programs)")
    conn.execute("DELETE FROM scores WHERE program_id NOT IN (SELECT id FROM programs)")


def get_event_info():
    """Return (school_name, event_name, year, logo_path) with sensible defaults."""
    school, event, year, logo = "Tournament", "Annual Sports Day", "", None
    try:
        df = run_query("SELECT * FROM event_info LIMIT 1")
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        r = df.iloc[0]
        school = r['school_name'] if pd.notna(r['school_name']) and r['school_name'] else school
        event = r['sports_name'] if pd.notna(r['sports_name']) and r['sports_name'] else event
        year = str(r['year']) if pd.notna(r['year']) else year
        logo = r['logo_path'] if pd.notna(r['logo_path']) and r['logo_path'] else None
    if logo and not os.path.exists(logo):
        logo = None
    if logo is None:
        logo = next((p for p in ("assets/logo.png", "assets/logo.jpg") if os.path.exists(p)), None)
    return school, event, year, logo


def get_setting(key, default=None):
    df = run_query("SELECT value FROM app_settings WHERE key = ?", (key,))
    return df.iloc[0]['value'] if not df.empty else default


def set_setting(key, value):
    with transaction() as conn:
        if value is None:
            conn.execute("DELETE FROM app_settings WHERE key = ?", (key,))
        else:
            conn.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )


def snapshot_database(reason):
    """Copy the current database into backups/ before a destructive action. Returns the path."""
    if not os.path.exists(DB_PATH):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(BACKUP_DIR, f"sports_manager_{reason}_{stamp}.db")
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(path)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    return path
