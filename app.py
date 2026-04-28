from flask import Flask, render_template, request, redirect
from models import (
    init_db, check_conflict, find_available_field,
    create_booking, get_all_bookings, get_booking_by_token,
    update_booking_status
)
from email_service import send_booking_email

app = Flask(__name__)

FIELDS = [
    "Sân pickleball số 1",
    "Sân pickleball số 2",
    "Sân pickleball số 3",
    "Sân bóng đá"
]

init_db()


# =========================
# ROUTES — PUBLIC
# =========================

@app.route('/')
def index():
    return render_template('index.html', fields=FIELDS)


@app.route('/book', methods=['POST'])
def book():
    data       = request.form
    name       = data.get('name', '').strip()
    company_id = data.get('company_id', '').strip()
    department = data.get('department', '').strip()
    field      = data.get('field', '').strip()
    date       = data.get('date', '').strip()
    start      = data.get('start', '').strip()
    end        = data.get('end', '').strip()

    if not all([name, company_id, department, field, date, start, end]):
        return render_template(
            'index.html', fields=FIELDS,
            error="Vui lòng điền đầy đủ thông tin."
        )

    if start >= end:
        return render_template(
            'index.html', fields=FIELDS,
            error="Giờ kết thúc phải sau giờ bắt đầu.",
            prev={'name': name, 'company_id': company_id,
                  'department': department, 'date': date,
                  'start': start, 'end': end}
        )

    conflicts = check_conflict(field, date, start, end)

    if conflicts:
        alt_field = find_available_field(FIELDS, date, start, end, exclude_field=field)
        if alt_field:
            return render_template(
                'index.html', fields=FIELDS,
                error=(
                    f"Sân '{field}' đã được đặt trong khung giờ {start}–{end}. "
                    f"Gợi ý: '{alt_field}' vẫn còn trống."
                ),
                suggested_field=alt_field,
                prev={'name': name, 'company_id': company_id,
                      'department': department, 'date': date,
                      'start': start, 'end': end}
            )
        else:
            return render_template(
                'index.html', fields=FIELDS,
                error=(
                    f"Không còn sân nào trống trong khung giờ {start}–{end}. "
                    f"Vui lòng chọn khung giờ khác."
                ),
                prev={'name': name, 'company_id': company_id,
                      'department': department, 'date': date,
                      'start': start, 'end': end}
            )

    booking_id = create_booking(name, company_id, department, field, date, start, end)
    send_booking_email(booking_id, name, department, field, date, start, end)
    return redirect('/history')


@app.route('/history')
def history():
    data = get_all_bookings()
    return render_template('history.html', data=data)


# =========================
# ROUTES — MANAGER (token-protected, no login needed)
# =========================

@app.route('/approve/<token>')
def approve(token):
    booking = get_booking_by_token(token)

    if not booking:
        return render_template('action_result.html',
                               icon="⚠️",
                               message="Liên kết không hợp lệ hoặc đã hết hạn.")

    if booking['status'] != 'pending':
        return render_template('action_result.html',
                               icon="ℹ️",
                               message=f"Booking này đã được xử lý (trạng thái: {booking['status']}).")

    update_booking_status(booking['id'], 'approved')
    return render_template('action_result.html',
                           icon="✅",
                           message=(
                               f"Đã chấp thuận đặt sân.<br>"
                               f"<strong>{booking['field']}</strong> – "
                               f"{booking['date']} – "
                               f"{booking['start_time']} đến {booking['end_time']}"
                           ))


@app.route('/reject/<token>')
def reject(token):
    booking = get_booking_by_token(token)

    if not booking:
        return render_template('action_result.html',
                               icon="⚠️",
                               message="Liên kết không hợp lệ hoặc đã hết hạn.")

    if booking['status'] != 'pending':
        return render_template('action_result.html',
                               icon="ℹ️",
                               message=f"Booking này đã được xử lý (trạng thái: {booking['status']}).")

    update_booking_status(booking['id'], 'rejected')
    return render_template('action_result.html',
                           icon="❌",
                           message=(
                               f"Đã từ chối đặt sân.<br>"
                               f"<strong>{booking['field']}</strong> – "
                               f"{booking['date']} – "
                               f"{booking['start_time']} đến {booking['end_time']}"
                           ))


# =========================
# ENTRY POINT
# =========================

if __name__ == '__main__':
    app.run(debug=True)