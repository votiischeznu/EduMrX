import logging

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.models.notifications import ContactMessage

logger = logging.getLogger(__name__)


def send_telegram_message(text: str) -> None:
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID

    if not bot_token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN yoki TELEGRAM_ADMIN_CHAT_ID sozlanmagan.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Telegramga xabar yuborishda xatolik: {e}")


@receiver(post_save, sender=ContactMessage)
def notify_admin_on_contact_message(sender, instance: ContactMessage, created, **kwargs):
    if not created:
        return

    text = (
        "📩 <b>Yangi xabar — EduMRX Contact</b>\n\n"
        f"👤 <b>Ism:</b> {instance.full_name}\n"
        f"📞 <b>Telefon:</b> {instance.phone}\n\n"
        f"💬 <b>Xabar:</b>\n{instance.message}"
    )
    send_telegram_message(text)