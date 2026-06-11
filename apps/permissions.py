from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    message = "Faqat tizim Super Admini uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role == "super-admin")
        )


class IsDirector(BasePermission):
    message = "Faqat Direktor uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "director"
        )


class IsCenterAdmin(BasePermission):
    message = "Faqat o'quv markazi Admini uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsTeacher(BasePermission):
    message = "Faqat O'qituvchi uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "teacher"
        )


class IsParent(BasePermission):
    message = "Faqat Ota-ona uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "parent"
        )


class IsStudent(BasePermission):
    message = "Faqat O'quvchi uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )
