import logging

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.models import ContactMessage, Notification, User
from apps.models.notifications import NotificationRecipient
from apps.pagination import CustomPagination
from apps.permissions import IsDirector, IsManager, IsSuperAdmin
from apps.serializers import (
    ContactMessageCreateSerializer,
    ContactMessageListSerializer,
    ContactMessageMarkReadSerializer,
)
from apps.serializers.notifications import NotificationRecipientSerializer
from apps.service.services import NotificationService

logger = logging.getLogger(__name__)


class NotificationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = NotificationRecipient.objects.select_related("notification", "notification__sender")
    serializer_class = NotificationRecipientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.for_user(self.request.user).order_by("-notification__created_at")

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        done = NotificationService.mark_read(user=request.user, notification_id=pk)
        return Response({"marked": done})

    @action(detail=False, methods=["post"], url_path="read-all")
    def mark_all_read(self, request):
        count = NotificationService.mark_all_read(user=request.user)
        return Response({"marked_count": count})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = NotificationService.unread_count(user=request.user)
        return Response({"unread": count})


@extend_schema(tags=["Contact"])
class ContactMessageCreateView(CreateAPIView):
    serializer_class = ContactMessageCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save()
        # Telegram xabari contact signal (apps/signals/contact.py) orqali
        # avtomatik yuboriladi — bu yerda qo'lda chaqirish shart emas.


@extend_schema(tags=["Contact"])
class ContactMessageListView(ListAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageListSerializer
    permission_classes = [IsSuperAdmin]


@extend_schema(tags=["Contact"])
class ContactMessageMarkReadView(UpdateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageMarkReadSerializer
    permission_classes = [IsSuperAdmin]
    http_method_names = ["patch"]


class SendNotificationInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    recipient_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    notification_type = serializers.ChoiceField(choices=Notification.Type.choices, default=Notification.Type.GENERAL)
    also_telegram = serializers.BooleanField(default=True)

    def validate_recipient_ids(self, value):
        valid_ids = list(
            User.objects.filter(
                id__in=value,
                role__in=[User.Role.PARENT, User.Role.STUDENT, User.Role.TEACHER],
            ).values_list("id", flat=True)
        )
        if not valid_ids:
            raise serializers.ValidationError(
                "Hech bo'lmaganda bitta to'g'ri qabul qiluvchi (Parent/Student/Teacher) bo'lishi shart."
            )
        return valid_ids


class _BaseSendNotificationView(APIView):
    serializer_class = SendNotificationInputSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        notification = NotificationService.send(
            title=data["title"],
            body=data["body"],
            recipient_ids=data["recipient_ids"],
            notification_type=data["notification_type"],
            sender=request.user,
            also_telegram=data["also_telegram"],
        )
        return Response(
            {
                "message": "Bildirishnoma yuborildi.",
                "notification_id": notification.id,
                "recipient_count": len(data["recipient_ids"]),
            },
            status=201,
        )


@extend_schema(tags=["Notifications"])
class ManagerSendNotificationView(_BaseSendNotificationView):
    permission_classes = [IsAuthenticated, IsManager]


@extend_schema(tags=["Notifications"])
class DirectorSendNotificationView(_BaseSendNotificationView):
    permission_classes = [IsAuthenticated, IsDirector]
