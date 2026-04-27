import requests

VIBER_TOKEN = "YOUR_VIBER_AUTH_TOKEN"

def send_viber_message(user_id, text, keyboard=None):
    url = "https://chatapi.viber.com/pa/send_message"

    headers = {
        "X-Viber-Auth-Token": VIBER_TOKEN
    }

    data = {
        "receiver": user_id,
        "type": "text",
        "text": text
    }

    if keyboard:
        data["keyboard"] = keyboard

    requests.post(url, json=data, headers=headers)


def build_approval_keyboard(booking_id):
    return {
        "Type": "keyboard",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "Text": "Chấp thuận",
                "ActionType": "reply",
                "ActionBody": f"approve_{booking_id}",
                "BgColor": "#2ecc71"
            },
            {
                "Columns": 3,
                "Rows": 1,
                "Text": "Từ chối",
                "ActionType": "reply",
                "ActionBody": f"reject_{booking_id}",
                "BgColor": "#e74c3c"
            }
        ]
    }