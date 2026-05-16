import uuid
from django.db import models
from apps.models.users import User
from django.db.models import DateField, CharField, UUIDField, TextChoices, DateTimeField, \
    Model, TextField, BooleanField, ForeignKey, Index, CASCADE

class Notification(Model):
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

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = ForeignKey(User, on_delete=CASCADE, related_name="notifications")

    type = CharField(max_length=30, choices=Type.choices, default=Type.GENERAL)
    channel = CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    title = CharField(max_length=255)
    body = TextField()

    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True, blank=True)
    sent_at = DateTimeField(null=True, blank=True)

    related_object_id = UUIDField(null=True, blank=True)
    related_object_type = CharField(max_length=100, blank=True)

    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["recipient", "is_read"]),
            Index(fields=["recipient", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.type}] → {self.recipient} | {'Read' if self.is_read else 'Unread'}"