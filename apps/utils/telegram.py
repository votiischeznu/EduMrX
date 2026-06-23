import requests
from django.conf import settings


def send_contact_message_to_telegram(contact_message):
    text = (
        "📩 Yangi murojaat\n\n"
        f"👤 Ism: {contact_message.full_name}\n"
        f"📞 Tel: +{contact_message.phone}\n"
        f"🏢 Markaz: {contact_message.center_name or '—'}\n"
        f"💬 Xabar: {contact_message.message}"
    )
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text},
            timeout=5,
        )
    except requests.RequestException:
        pass