from rest_framework.serializers import ModelSerializer, SerializerMethodField

from apps.models.notifications import Notification, NotificationRecipient


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
