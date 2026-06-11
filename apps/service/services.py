from django.db import transaction
from django.utils import timezone
from apps.models import Notification, NotificationRecipient, BaseModel, GroupStudent


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
    ) -> Notification:
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

        return notification

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