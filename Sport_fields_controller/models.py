import sqlite3

DB_NAME = "database.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        company_id TEXT,
        department TEXT,
        field TEXT,
        date TEXT,
        start_time TEXT,
        end_time TEXT,
        status TEXT
    )
    """)
    conn.commit()


# =========================
# BOOKING LOGIC
# =========================

def check_conflict(field, date, start, end):
    conn = get_db()

    query = """
    SELECT * FROM bookings
    WHERE field=? AND date=? 
    AND NOT (end_time <= ? OR start_time >= ?)
    AND status='approved'
    """

    return conn.execute(query, (field, date, start, end)).fetchall()


def find_available_field(fields, date, start, end):
    conn = get_db()

    query = """
    SELECT * FROM bookings
    WHERE field=? AND date=? 
    AND NOT (end_time <= ? OR start_time >= ?)
    AND status='approved'
    """

    for f in fields:
        result = conn.execute(query, (f, date, start, end)).fetchall()
        if not result:
            return f

    return None


def create_booking(name, company_id, department, field, date, start, end):
    conn = get_db()

    cursor = conn.execute("""
    INSERT INTO bookings 
    (name, company_id, department, field, date, start_time, end_time, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (name, company_id, department, field, date, start, end))

    conn.commit()
    return cursor.lastrowid


def get_all_bookings():
    conn = get_db()
    return conn.execute("SELECT * FROM bookings ORDER BY date DESC").fetchall()


def get_pending_bookings():
    conn = get_db()
    return conn.execute("SELECT * FROM bookings WHERE status='pending'").fetchall()


def update_booking_status(booking_id, status):
    conn = get_db()
    conn.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
    conn.commit()