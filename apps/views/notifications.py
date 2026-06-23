from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.models import ContactMessage
from apps.models.notifications import NotificationRecipient
from apps.permissions import IsSuperAdmin
from apps.serializers import ContactMessageCreateSerializer, ContactMessageListSerializer
from apps.serializers.notifications import NotificationRecipientSerializer
from apps.service.services import NotificationService
from apps.utils.telegram import send_contact_message_to_telegram
from apps.pagination import CustomPagination
from apps.serializers import ContactMessageMarkReadSerializer


class NotificationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = NotificationRecipient.objects.select_related("notification", "notification__sender")
    serializer_class = NotificationRecipientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.for_user(self.request.user).order_by("-notification__created_at")

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
        contact_message = serializer.save()
        send_contact_message_to_telegram(contact_message)


@extend_schema(tags=["SuperAdminContact"])
class SuperAdminContactMessageListView(ListAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageListSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at", "is_read"]
    ordering = ["-created_at"]


@extend_schema(tags=["SuperAdminContact"])
class SuperAdminContactMessageMarkReadView(UpdateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageMarkReadSerializer
    permission_classes = [IsSuperAdmin]
    http_method_names = ["patch"]

    def perform_update(self, serializer):
        serializer.save(is_read=True)
