import re

from rest_framework.serializers import ModelSerializer, SerializerMethodField, ValidationError

from apps.models.notifications import ContactMessage, Notification, NotificationRecipient


class NotificationSerializer(ModelSerializer):
    sender_name = SerializerMethodField()
    unread_count = SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "channel",
            "title",
            "body",
            "sender",
            "sender_name",
            "sent_at",
            "related_object_id",
            "related_object_type",
            "created_at",
            "unread_count",
        ]
        read_only_fields = ["id", "created_at", "sent_at", "sender"]

    def get_sender_name(self, obj):
        return str(obj.sender) if obj.sender else "System"

    def get_unread_count(self, obj):
        return obj.recipients.filter(is_read=False).count()


class NotificationRecipientSerializer(ModelSerializer):
    notification = NotificationSerializer(read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = ["id", "notification", "is_read", "read_at"]
        read_only_fields = ["id", "read_at"]


class SendNotificationSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "type",
            "channel",
            "title",
            "body",
            "related_object_id",
            "related_object_type",
        ]


class ContactMessageCreateSerializer(ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["full_name", "phone", "center_name", "message"]

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)

        if digits.startswith("998") and len(digits) == 12:
            normalized = f"+{digits}"
        elif len(digits) == 9:
            normalized = f"+998{digits}"
        else:
            raise ValidationError("Telefon raqam noto'g'ri formatda. Masalan: +998 90 123 45 67")

        return normalized


class ContactMessageListSerializer(ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "full_name", "phone", "center_name", "message", "is_read", "created_at"]
        read_only_fields = ["id", "full_name", "phone", "center_name", "message", "created_at"]


class ContactMessageMarkReadSerializer(ModelSerializer):
    """Faqat is_read maydonini patch qilish uchun."""

    class Meta:
        model = ContactMessage
        fields = ["is_read"]
