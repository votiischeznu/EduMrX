from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.models.notifications import NotificationRecipient
from apps.serializers.notifications_serializer import NotificationRecipientSerializer
from apps.services import NotificationService


class NotificationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationRecipientSerializer

    def get_queryset(self):
        return (
            NotificationRecipient.objects
            .filter(recipient=self.request.user)
            .select_related("notification", "notification__sender")
            .order_by("-notification__created_at")
        )

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
