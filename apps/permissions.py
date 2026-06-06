from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    message = "Faqat Super Admin uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )
