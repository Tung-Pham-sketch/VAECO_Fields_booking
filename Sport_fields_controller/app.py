from flask import Flask, render_template, request, redirect
from viber import send_viber_message, build_approval_keyboard
import sqlite3

app = Flask(__name__)

MANAGER_VIBER_ID = None

FIELDS = [
    "Sân pickleball số 1",
    "Sân pickleball số 2",
    "Sân pickleball số 3",
    "Sân bóng đá"
]

def get_db():
    conn = sqlite3.connect("database.db")
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

init_db()

@app.route('/')
def index():
    return render_template('index.html', fields=FIELDS)

@app.route('/book', methods=['POST'])

def send_viber_booking(booking_id, name, field, date, start, end):
    global MANAGER_VIBER_ID

    if not MANAGER_VIBER_ID:
        print("Manager chưa connect Viber")
        return

    text = f"""
📢 Đăng ký sân mới

👤 {name}
🏟 {field}
📅 {date}
⏰ {start} - {end}
"""

    keyboard = build_approval_keyboard(booking_id)

    send_viber_message(MANAGER_VIBER_ID, text, keyboard)

def book():
    data = request.form
    name = data['name']
    company_id = data['company_id']
    department = data['department']
    field = data['field']
    date = data['date']
    start = data['start']
    end = data['end']

    conn = get_db()

    # Check overlap
    query = """
    SELECT * FROM bookings
    WHERE field=? AND date=? 
    AND NOT (end_time <= ? OR start_time >= ?)
    AND status='approved'
    """
    conflict = conn.execute(query, (field, date, start, end)).fetchall()

    if conflict:
        # Suggest other fields
        for f in FIELDS:
            alt = conn.execute(query, (f, date, start, end)).fetchall()
            if not alt:
                return f"Sân đã bị đặt. Gợi ý: {f} còn trống."

        return f"Không còn sân nào trống trong khung giờ {start}-{end}"

    # Save booking
    conn.execute("""
    INSERT INTO bookings 
    (name, company_id, department, field, date, start_time, end_time, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (name, company_id, department, field, date, start, end))

    conn.commit()

    return redirect('/history')

@app.route('/history')
def history():
    conn = get_db()
    data = conn.execute("SELECT * FROM bookings ORDER BY date DESC").fetchall()
    return render_template('history.html', data=data)

@app.route('/manager')
def manager():
    conn = get_db()
    data = conn.execute("SELECT * FROM bookings WHERE status='pending'").fetchall()
    return render_template('manager.html', data=data)

@app.route('/approve/<int:id>')
def approve(id):
    conn = get_db()
    conn.execute("UPDATE bookings SET status='approved' WHERE id=?", (id,))
    conn.commit()
    return redirect('/manager')

@app.route('/reject/<int:id>')
def reject(id):
    conn = get_db()
    conn.execute("UPDATE bookings SET status='rejected' WHERE id=?", (id,))
    conn.commit()
    return redirect('/manager')



app.run(debug=True)