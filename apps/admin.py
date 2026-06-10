from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from apps.models import (
    User,
    Room,
    Group,
    GroupStudent,
    Attendance,
    Student,
    Teacher,
    Parent,
    Center,
    CenterStaff,
    Course,
    Lesson,
    Payment,
    Debt,
    Notification,
    NotificationRecipient,
)

admin.site.site_header = "EduMrX1 Boshqaruv Paneli"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Tizim Modellari Ro'yxati"


@admin.register(User)
class UserModelView(UserAdmin):
    list_display = (
        "phone",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = ("role", "is_staff", "is_active", "is_superuser")
    search_fields = ("phone", "first_name", "last_name", "email")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            _("Shaxsiy Ma'lumotlar"),
            {"fields": ("first_name", "last_name", "email", "role", "avatar")},
        ),
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
        (
            _("Shaxsiy Ma'lumotlar"),
            {"fields": ("first_name", "last_name", "email", "role")},
        ),
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


@admin.register(Center)
class CenterAdmin(ModelAdmin):
    list_display = ["id", "name", "phone", "email", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "phone", "email", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CenterStaff)
class CenterStaffAdmin(ModelAdmin):
    list_display = ["id", "user", "center", "created_at"]
    list_filter = ["center"]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__phone",
        "center__name",
    ]
    autocomplete_fields = ["user"]


@admin.register(Parent)
class ParentAdmin(ModelAdmin):
    list_display = ["id", "get_full_name", "occupation"]
    search_fields = ["user__first_name", "user__last_name", "user__phone", "occupation"]
    autocomplete_fields = ["user"]

    def get_full_name(self, obj):
        if obj.user:
            return (
                f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.phone
            )
        return "-"

    get_full_name.short_description = _("Ota-ona ismi")


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ["id", "get_full_name", "center", "status", "enrolled_at"]
    list_filter = ["status", "center", "enrolled_at"]
    search_fields = ["user__first_name", "user__last_name", "user__phone", "address"]
    autocomplete_fields = ["user", "parent"]
    ordering = ["-enrolled_at"]

    def get_full_name(self, obj):
        if obj.user:
            return (
                f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.phone
            )
        return "-"

    get_full_name.short_description = _("Talaba ismi")


@admin.register(Teacher)
class TeacherAdmin(ModelAdmin):
    list_display = ["id", "get_full_name", "specialization", "salary", "experience"]
    list_filter = ["specialization", "experience"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    autocomplete_fields = ["user"]

    def get_full_name(self, obj):
        if obj.user:
            return (
                f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.phone
            )
        return "-"

    get_full_name.short_description = _("O'qituvchi ismi")


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ["id", "name", "duration_months", "price", "status", "center"]
    list_filter = ["status", "center", "duration_months"]
    search_fields = ["name", "description"]


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ["id", "group", "date", "start_time", "end_time", "topic"]
    list_filter = ["date", "group__course", "group"]
    search_fields = ["topic", "group__name"]
    raw_id_fields = ["group"]


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ["id", "lesson", "get_student", "status", "marked_at"]
    list_filter = ["status", "lesson__group", "lesson__date"]
    search_fields = [
        "student__user__first_name",
        "student__user__last_name",
        "lesson__group__name",
    ]
    raw_id_fields = ["lesson", "student"]

    def get_student(self, obj):
        if obj.student and obj.student.user:
            user = obj.student.user
            return f"{user.first_name} {user.last_name}".strip() or user.phone
        return "-"

    get_student.short_description = _("Talaba")


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ["id", "name", "capacity"]
    search_fields = ["name"]


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = [
        "id",
        "name",
        "course",
        "teacher",
        "room",
        "status",
        "student_count",
    ]
    list_filter = ["status", "course", "room"]
    search_fields = ["name"]


@admin.register(GroupStudent)
class GroupStudentAdmin(ModelAdmin):
    list_display = ["id", "group", "student", "joined_at", "is_active"]
    list_filter = ["is_active", "group"]
    search_fields = [
        "student__user__first_name",
        "student__user__last_name",
        "group__name",
    ]
    raw_id_fields = ["group", "student"]


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = [
        "id",
        "student",
        "group",
        "amount",
        "discount",
        "final_amount",
        "method",
        "status",
        "paid_at",
    ]
    list_filter = ["status", "method", "status", "created_at"]
    search_fields = [
        "student__user__first_name",
        "student__user__last_name",
        "group__name",
        "period_month",
    ]
    raw_id_fields = ["student", "group"]


@admin.register(Debt)
class DebtAdmin(ModelAdmin):
    list_display = ["id", "student", "group", "amount", "due_date", "status"]
    list_filter = ["status", "due_date"]
    search_fields = [
        "student__user__first_name",
        "student__user__last_name",
        "group__name",
    ]
    raw_id_fields = ["student", "group"]


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ["id", "title", "type", "channel", "sender", "created_at"]
    list_filter = ["type", "channel", "created_at"]
    search_fields = ["title", "body", "sender__phone"]
    raw_id_fields = ["sender"]


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(ModelAdmin):
    list_display = ["id", "notification", "recipient", "is_read", "read_at"]
    list_filter = ["is_read", "read_at"]
    search_fields = [
        "recipient__first_name",
        "recipient__last_name",
        "recipient__phone",
        "notification__title",
    ]
    raw_id_fields = ["notification", "recipient"]
