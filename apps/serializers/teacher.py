from datetime import timedelta

from django.utils import timezone
from rest_framework.fields import UUIDField, CharField, SerializerMethodField, IntegerField, ChoiceField
from rest_framework.serializers import Serializer, ModelSerializer

from apps.models import Attendance, Group, Lesson, Teacher


class StudentShortSerializer(Serializer):
    id = UUIDField()
    full_name = CharField()
    phone = CharField()


class TeacherGroupSerializer(ModelSerializer):
    room = SerializerMethodField()
    student_count = IntegerField(source="active_student_count", read_only=True)
    students = SerializerMethodField()
    lesson_days = SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "room",
            "student_count",
            "students",
            "lesson_days",
            "lesson_start_time",
            "lesson_end_time",
        ]

    def get_room(self, obj):
        return obj.room.name if obj.room_id else None

    def get_students(self, obj):
        active_enrollments = obj.enrollments.filter(
            is_active=True, student__user__is_deleted=False
        ).select_related("student__user")
        return StudentShortSerializer(
            [e.student for e in active_enrollments], many=True
        ).data

    def get_lesson_days(self, obj):
        return [Group.DayOfWeek(day).label for day in obj.lesson_days]


class TeacherSalarySerializer(ModelSerializer):
    # To'lov sanasi/tarixi saqlanmaydi — Teacher.created_at'dan boshlab
    # har 30 kunda takrorlanadi deb hisoblanadi.
    next_payment_date = SerializerMethodField()
    days_remaining = SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ["salary", "next_payment_date", "days_remaining"]

    def get_next_payment_date(self, obj):
        return self._next_cycle_date(obj)

    def get_days_remaining(self, obj):
        return (self._next_cycle_date(obj) - timezone.now().date()).days

    @staticmethod
    def _next_cycle_date(obj):
        created = obj.created_at.date()
        today = timezone.now().date()
        days_passed = (today - created).days
        cycles_passed = days_passed // 30
        return created + timedelta(days=30 * (cycles_passed + 1))


class TeacherLessonSerializer(ModelSerializer):
    group_name = CharField(source="group.name", read_only=True)
    course_name = CharField(source="group.course.name", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "group",
            "group_name",
            "course_name",
            "date",
            "start_time",
            "end_time",
            "topic",
            "notes",
        ]
        # Teacher faqat mavzu/izohni kiritadi — sana/vaqt guruh jadvalidan keladi
        read_only_fields = ["group", "date", "start_time", "end_time"]


class AttendanceMarkSerializer(Serializer):
    student = UUIDField()
    status = ChoiceField(choices=Attendance.Status.choices)
    note = CharField(required=False, allow_blank=True, max_length=300)


class AttendanceSerializer(ModelSerializer):
    class Meta:
        model = Attendance
        fields = ["id", "student", "status", "note", "marked_at"]