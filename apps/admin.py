from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from apps.models import Room, Group, GroupStudent, Attendance, Student, Teacher, Parent, User

admin.site.site_header = "EduMrX1 Boshqaruv Paneli"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Tizim Modellari Ro'yxati"


@admin.register(User)
class UserModelView(UserAdmin):
    list_display = ("phone", "first_name", "last_name", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_active", "is_superuser")
    search_fields = ("phone", "first_name", "last_name", "email")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("Shaxsiy Ma'lumotlar"), {"fields": ("first_name", "last_name", "email", "role", "avatar")}),
        (
            _("Huquqlar & Rollar (SuperAdmin/Admin yaratish)"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Muhim sanalar"), {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("Shaxsiy Ma'lumotlar"), {"fields": ("first_name", "last_name", "email", "role", "branch")}),
        (_("Shaxsiy Ma'lumotlar"), {"fields": ("first_name", "last_name", "email", "role")}),
        (
            _("Huquqlar"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")


@admin.register(Parent)
class ParentAdmin(ModelAdmin):
    list_display = ['id', 'get_full_name', 'occupation']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    autocomplete_fields = ['user']

    def get_full_name(self, obj):
        return obj.user.full_name if obj.user else "-"
    get_full_name.short_description = _("Ota-ona ismi")


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ['id', 'name', 'capacity']
    search_fields = ['name']


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ['id', 'name', 'course', 'teacher', 'room', 'status', 'lesson_start_time']
    list_filter = ['status', 'course', 'room']
    search_fields = ['name']


@admin.register(GroupStudent)
class GroupStudentAdmin(ModelAdmin):
    list_display = ['id', 'group', 'student', 'joined_at', 'is_active']
    list_filter = ['is_active', 'group']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'group__name']
    raw_id_fields = ['group', 'student']


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ['id', 'get_full_name', 'center', 'status', 'enrolled_at']
    list_filter = ['status', 'center', 'enrolled_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'address']
    autocomplete_fields = ['user', 'parent']
    ordering = ['-enrolled_at']

    def get_full_name(self, obj):
        return obj.user.full_name if obj.user else "-"
    get_full_name.short_description = _("Talaba ismi")


@admin.register(Teacher)
class TeacherAdmin(ModelAdmin):
    list_display = ['id', 'get_full_name', 'specialization', 'salary', 'experience']
    list_filter = ['specialization', 'experience']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    autocomplete_fields = ['user']

    def get_full_name(self, obj):
        return obj.user.full_name if obj.user else "-"
    get_full_name.short_description = _("O'qituvchi ismi")


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ['id', 'lesson', 'get_student', 'status', 'marked_at']
    list_filter = ['status', 'lesson__group', 'lesson__date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'lesson__group__name']
    raw_id_fields = ['lesson', 'student']

    def get_student(self, obj):
        return obj.student.user.full_name if obj.student and obj.student.user else "-"
    get_student.short_description = _("Talaba")