import sqlite3
import secrets

import os
# On Render the persistent disk is mounted at /data.
# Locally it falls back to a file in the current directory.
DB_NAME = os.environ.get("DB_PATH", "database.db")


def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create the bookings table if it doesn't exist, then run any
    missing-column migrations so existing databases stay compatible.
    """
    conn = get_db()
    try:
        # Create table (no-op if already exists)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT,
            company_id  TEXT,
            department  TEXT,
            field       TEXT,
            date        TEXT,
            start_time  TEXT,
            end_time    TEXT,
            status      TEXT,
            token       TEXT UNIQUE
        )
        """)
        conn.commit()

        # Migration: add token column if it was created before this column existed
        existing_columns = [
            row[1] for row in conn.execute("PRAGMA table_info(bookings)").fetchall()
        ]
        if "token" not in existing_columns:
            print("[DB] Migrating: adding token column to bookings table.")
            conn.execute("ALTER TABLE bookings ADD COLUMN token TEXT")
            conn.commit()

    finally:
        conn.close()


# =========================
# BOOKING LOGIC
# =========================

CONFLICT_QUERY = """
SELECT * FROM bookings
WHERE field=? AND date=?
AND NOT (end_time <= ? OR start_time >= ?)
AND status != 'rejected'
"""
# Checks against both 'pending' and 'approved' to prevent double-booking
# while a request is awaiting manager decision.


def check_conflict(field, date, start, end):
    """Return all conflicting bookings for the given field/date/time range."""
    conn = get_db()
    try:
        return conn.execute(CONFLICT_QUERY, (field, date, start, end)).fetchall()
    finally:
        conn.close()


def find_available_field(fields, date, start, end, exclude_field=None):
    """
    Return the first field in `fields` that has no conflict.
    Pass `exclude_field` to skip the field the user already tried.
    Returns None if every field is taken.
    """
    conn = get_db()
    try:
        for f in fields:
            if f == exclude_field:
                continue
            result = conn.execute(CONFLICT_QUERY, (f, date, start, end)).fetchall()
            if not result:
                return f
        return None
    finally:
        conn.close()


def create_booking(name, company_id, department, field, date, start, end):
    """Insert a new booking with status='pending', generate a unique token, return row id."""
    conn = get_db()
    try:
        token = secrets.token_urlsafe(32)   # 256-bit random token
        cursor = conn.execute("""
        INSERT INTO bookings
        (name, company_id, department, field, date, start_time, end_time, status, token)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (name, company_id, department, field, date, start, end, token))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_bookings():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM bookings ORDER BY date DESC, start_time ASC"
        ).fetchall()
    finally:
        conn.close()


def get_pending_bookings():
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM bookings WHERE status='pending' ORDER BY date ASC, start_time ASC"
        ).fetchall()
    finally:
        conn.close()


def get_booking_by_id(booking_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM bookings WHERE id=?", (booking_id,)
        ).fetchone()
    finally:
        conn.close()


def get_booking_by_token(token):
    """Look up a booking by its one-time approval token."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM bookings WHERE token=?", (token,)
        ).fetchone()
    finally:
        conn.close()


def update_booking_status(booking_id, status):
    """Update booking status. Valid values: 'approved', 'rejected'."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE bookings SET status=? WHERE id=?", (status, booking_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_old_bookings(days=7):
    """Delete all bookings whose date is more than `days` days in the past."""
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM bookings WHERE date(date) < date('now', ?)",
            (f"-{days} days",)
        )
        conn.commit()
        print(f"[Cleanup] Đã xoá các booking cũ hơn {days} ngày.")
    finally:
        conn.close()
