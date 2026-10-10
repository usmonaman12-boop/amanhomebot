import requests
from django.conf import settings


def send_telegram_message(chat_id, text):
    """Send a message to a Telegram chat using the bot token in settings.
    Fails silently (returns False) if the token/chat_id is missing or the
    request errors out, so it never breaks the teacher's flow."""
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=8,
        )
        return resp.ok
    except requests.RequestException:
        return False
