"""
O'quv markazi xizmatlari uchun yagona servislar to'plami.
"""
import logging

from django.db import transaction
from django.utils import timezone

from apps.models import (
    NotificationRecipient,
    User,
    GroupStudent,
)
from apps.tasks.telegram import send_telegram_bulk_message_task

logger = logging.getLogger(__name__)

NOTIFIABLE_ROLES = [User.Role.DIRECTOR, User.Role.ADMIN, User.Role.TEACHER]


class NotificationService:
    @staticmethod
    def send_notification(*, recipient_ids: list[str], title: str, body: str):
        """
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

        # Asinxron yuborish uchun Celery task'ni chaqiramiz
        send_telegram_bulk_message_task.delay(chat_ids, text)
        logger.info("Telegram notification yuborish uchun task ishga tushirildi.")

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
