"""
ContactMessage yaratilganda FAQAT role=SUPER_ADMIN bo'lgan
foydalanuvchilarga Telegram orqali xabar yuboradi. Boshqa rollarga
(Director, Manager, Teacher, Parent, Student) bu signal orqali
hech qachon xabar bormaydi.

apps/apps.py ichida ready() metodida import qilinishi kerak:

    class AppsConfig(AppConfig):
        def ready(self):
            import apps.signals.contact  # noqa
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.models import ContactMessage, User
from apps.service.telegram_bot import TelegramBotService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ContactMessage)
def notify_on_new_contact_message(sender, instance: ContactMessage, created: bool, **kwargs):
    if not created:
        return

    superadmin_chat_ids = list(
        User.objects.filter(
            role=User.Role.SUPER_ADMIN,
            telegram_id__isnull=False,
        ).values_list("telegram_id", flat=True)
    )

    if not superadmin_chat_ids:
        logger.info("ContactMessage keldi, lekin Telegramga ulangan SuperAdmin topilmadi.")
        return

    text = (
        "📩 Yangi murojaat\n\n"
        f"👤 Ism: {instance.full_name}\n"
        f"📞 Tel: {instance.phone}\n"
        f"🏢 Markaz: {instance.center_name or '—'}\n"
        f"💬 Xabar: {instance.message}"
    )

    try:
        result = TelegramBotService.send_bulk(superadmin_chat_ids, text, parse_mode=None)
        logger.info(
            "ContactMessage Telegram xabari: sent=%s failed=%s",
            result["sent"], result["failed"],
        )
    except Exception as e:
        logger.error("ContactMessage Telegram xabarini yuborishda xatolik: %s", e)