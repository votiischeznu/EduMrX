from django.db.models import (
    CharField,
    UUIDField,
    TextChoices,
    DateTimeField,
    TextField,
    BooleanField,
    ForeignKey,
    Index,
    CASCADE,
    SET_NULL,
)

from apps.models import BaseModel


class Notification(BaseModel):
    class Type(TextChoices):
        PAYMENT_DUE = "payment_due", "Payment Due"
        PAYMENT_RECEIVED = "payment_received", "Payment Received"
        ATTENDANCE_ALERT = "attendance_alert", "Attendance Alert"
        GENERAL = "general", "General"
        EXAM_REMINDER = "exam_reminder", "Exam Reminder"
        HOMEWORK = "homework", "Homework"

    class Channel(TextChoices):
        IN_APP = "in_app", "In-App"
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"

    sender = ForeignKey(
        "apps.User",
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )

    type = CharField(max_length=30, choices=Type.choices, default=Type.GENERAL)
    channel = CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    title = CharField(max_length=255)
    body = TextField()
    sent_at = DateTimeField(null=True, blank=True)
    related_object_id = UUIDField(null=True, blank=True)
    related_object_type = CharField(max_length=100, blank=True)

    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.type}] {self.title} | from {self.sender or 'System'}"


class NotificationRecipient(BaseModel):
    notification = ForeignKey(
        Notification, on_delete=CASCADE, related_name="recipients"
    )
    recipient = ForeignKey(
        "apps.User", on_delete=CASCADE, related_name="notification_recipients"
    )

    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("notification", "recipient")
        indexes = [
            Index(fields=["recipient", "is_read"]),
            Index(fields=["recipient", "notification"]),
        ]

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.recipient} | {self.notification.title} | {status}"
