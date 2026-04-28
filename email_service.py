import smtplib
from email.mime.text import MIMEText
from models import get_booking_by_id

EMAIL_SENDER  = "vaecohcmsport@gmail.com"
EMAIL_PASSWORD = "zzwuehzvrolfdemg"
EMAIL_MANAGER = "tungpham23801@gmail.com"

# Set this to your deployed URL once live, e.g. "https://vaeco-sport.onrender.com"
# During local testing keep it as localhost.
BASE_URL = "https://vaeco-fields-booking.onrender.com"


def send_booking_email(booking_id, name, department, field, date, start, end):
    """
    Send manager a notification email with secure one-click approve/reject links.
    Each link contains the booking's unique token — no login required, and the
    /manager page is no longer publicly accessible.
    """
    # Fetch the token that was stored when the booking was created
    booking = get_booking_by_id(booking_id)
    if not booking:
        print(f"[Email] Booking #{booking_id} không tồn tại — bỏ qua email.")
        return
    token = booking["token"]

    approve_url = f"{BASE_URL}/approve/{token}"
    reject_url  = f"{BASE_URL}/reject/{token}"

    subject = f"[Booking #{booking_id}] Yêu cầu đặt sân – {field} – {date}"

    body = f"""Có yêu cầu đặt sân mới:

👤 {name} ({department})
🏟  {field}
📅 {date}
⏰ {start} - {end}

── Hành động nhanh ──────────────────────────
✅ Chấp thuận:
{approve_url}

❌ Từ chối:
{reject_url}
─────────────────────────────────────────────

Mỗi liên kết chỉ hoạt động một lần và chỉ dành cho booking này.
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From']    = EMAIL_SENDER
    msg['To']      = EMAIL_MANAGER

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"[Email] Đã gửi thông báo booking #{booking_id} tới {EMAIL_MANAGER}")
    except smtplib.SMTPAuthenticationError:
        print("[Email] Lỗi xác thực Gmail — kiểm tra lại App Password.")
    except smtplib.SMTPException as e:
        print(f"[Email] Lỗi SMTP: {e}")
    except Exception as e:
        print(f"[Email] Lỗi không xác định: {e}")
