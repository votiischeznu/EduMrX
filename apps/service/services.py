# apps/service/services.py
import logging

from django.db import transaction
from django.utils import timezone

from apps.models import GroupStudent, Notification, NotificationRecipient, User
from apps.service.telegram_bot import TelegramBotService

logger = logging.getLogger(__name__)

NOTIFIABLE_ROLES = [User.Role.PARENT, User.Role.STUDENT, User.Role.TEACHER]


class NotificationService:
    @staticmethod
    def send(
        *,
        title: str,
        body: str,
        recipient_ids: list,
        notification_type: str = Notification.Type.GENERAL,
        channel: str = Notification.Channel.IN_APP,
        sender=None,
        related_object_id=None,
        related_object_type="",
        also_telegram: bool = False,
    ) -> Notification:
        """
        also_telegram=True bo'lsa, in-app notification yaratilgandan tashqari,
        recipient_ids ichidan FAQAT role IN (PARENT, STUDENT, TEACHER) bo'lgan
        va telegram_id'si bor foydalanuvchilarga Telegram orqali ham xabar
        boradi. Boshqa rollar (Manager, Director, SuperAdmin) bu orqali
        Telegram xabar olmaydi — chunki ular bu funksiyada xabar YUBORUVCHI
        tomon hisoblanadi.

        Telegram yuborilmasa ham (token yo'q, chat topilmadi va h.k.),
        in-app notification baribir yaratiladi.
        """
        notification = Notification.objects.create(
            title=title,
            body=body,
            type=notification_type,
            channel=channel,
            sender=sender,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            sent_at=timezone.now(),
        )

        NotificationRecipient.objects.bulk_create(
            [
                NotificationRecipient(notification=notification, recipient_id=uid)
                for uid in recipient_ids
            ],
            ignore_conflicts=True,
        )

        if also_telegram:
            NotificationService._send_telegram_for_recipients(
                recipient_ids=recipient_ids, title=title, body=body
            )

        return notification

    @staticmethod
    def _send_telegram_for_recipients(*, recipient_ids: list, title: str, body: str):
        """
        FAQAT role IN (PARENT, STUDENT, TEACHER) bo'lganlarga yuboriladi.
        Bu filter ataylab shu yerda turadi — chaqiruvchi kod bu cheklovni
        chetlab o'tolmaydi.
        """
        chat_ids = list(
            User.objects.filter(
                id__in=recipient_ids,
                role__in=NOTIFIABLE_ROLES,
                telegram_id__isnull=False,
            ).values_list("telegram_id", flat=True)
        )

        if not chat_ids:
            return

        text = f"<b>{title}</b>\n\n{body}"

        try:
            result = TelegramBotService.send_bulk(chat_ids, text)
            logger.info(
                "Telegram notification yuborildi: sent=%s failed=%s",
                result["sent"], result["failed"],
            )
        except Exception as e:
            logger.error("Telegram notification yuborishda xatolik: %s", e)

    @staticmethod
    def mark_read(*, user, notification_id) -> bool:
        updated = NotificationRecipient.objects.filter(
            recipient=user,
            notification_id=notification_id,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        return updated > 0

    @staticmethod
    def mark_all_read(*, user) -> int:
        return NotificationRecipient.objects.filter(
            recipient=user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())

    @staticmethod
    def unread_count(*, user) -> int:
        return NotificationRecipient.objects.filter(
            recipient=user,
            is_read=False,
        ).count()


def move_or_add_student(student, target_group, old_group=None):
    with transaction.atomic():
        if old_group:
            GroupStudent.objects.filter(student=student, group=old_group).delete()

        return GroupStudent.objects.create(student=student, group=target_group)