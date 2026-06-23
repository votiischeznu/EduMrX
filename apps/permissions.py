from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    message = "Faqat tizim Super Admini uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)


class IsDirector(BasePermission):
    message = "Faqat Direktor uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_director)


class IsManager(BasePermission):
    message = "Faqat o'quv markazi Admini uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)


class IsTeacher(BasePermission):
    message = "Faqat O'qituvchi uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_teacher)


class IsParent(BasePermission):
    message = "Faqat Ota-ona uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_parent)


class IsStudent(BasePermission):
    message = "Faqat O'quvchi uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_student)
