from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    message = "Faqat tizim Super Admini uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        # FIX: is_superuser (Django'ning ichki auth maydoni) emas,
        # is_super_admin (role=SUPER_ADMIN'ga asoslangan property) tekshiriladi.
        # is_superuser bilan role mos kelmasligi mumkin edi (masalan API
        # orqali yaratilgan super_admin role'li user is_superuser=False
        # bo'lishi mumkin edi).
        return bool(user and user.is_authenticated and user.is_active and user.is_super_admin)


class IsDirector(BasePermission):
    message = "Faqat Direktor uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_director)


class IsManager(BasePermission):
    message = "Faqat o'quv markazi Admini uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_admin)


class IsTeacher(BasePermission):
    message = "Faqat O'qituvchi uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_teacher)


class IsParent(BasePermission):
    message = "Faqat Ota-ona uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_parent)


class IsStudent(BasePermission):
    message = "Faqat O'quvchi uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_student)


class IsAdminOrDirector(BasePermission):
    """
    YANGI: dashboard.py -> AdminDashboardView ichida qo'lda yozilgan
    `if not (user.is_admin or user.is_director): return 403` tekshiruvi
    o'rniga. Endi permission_classes orqali izchil ishlaydi — schema
    generatsiyasida ham to'g'ri ko'rinadi, view logikasidan ajratilgan.
    """

    message = "Faqat Admin (Reception) yoki Direktor uchun ruxsat berilgan."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and (user.is_admin or user.is_director))


class IsManagerOrDirectorOrSuperAdmin(BasePermission):
    """
    YANGI: attendance.py -> AttendanceOverviewAPIView uchun. Bu view
    hozircha IsAuthenticated bilan HAR QANDAY rol (student/parent/teacher
    ham) uchun ochiq va queryset markaz/filial bo'yicha cheklanmagan —
    butun platforma davomatini ko'rsatadi. Permission darajasida buni
    boshqaruv rollariga cheklab qo'yish kerak; lekin bu YAGONA yechim
    emas — get()dagi Attendance.objects.filter(...) ham albatta
    markaz/filial bo'yicha scoping olishi shart (bu alohida, queryset
    darajasidagi tuzatish, permission emas).
    """
    message = "Faqat Admin, Direktor yoki Super Admin uchun ruxsat berilgan."
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (user.is_admin or user.is_director or user.is_super_admin)
        )