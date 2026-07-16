from django.utils import timezone
from rest_framework.fields import CharField, SerializerMethodField, UUIDField, DateField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models import Attendance, Course, Group, Lesson, Teacher


class CourseMiniSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "duration_months", "price"]


class TeacherMiniSerializer(ModelSerializer):
    full_name = CharField(read_only=True)
    phone = CharField(read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "full_name", "phone", "specialization"]


class ScheduleSerializer(Serializer):
    """Group.lesson_days ni odam o'qiydigan formatga o'giradi."""

    days = SerializerMethodField()
    start_time = SerializerMethodField()
    end_time = SerializerMethodField()

    def get_days(self, group):
        day_labels = dict(Group.DayOfWeek.choices)
        return [day_labels.get(day, str(day)) for day in group.lesson_days]

    def get_start_time(self, group):
        return group.lesson_start_time.strftime("%H:%M")

    def get_end_time(self, group):
        return group.lesson_end_time.strftime("%H:%M")


class StudentGroupSerializer(ModelSerializer):
    course = CourseMiniSerializer(read_only=True)
    teacher = TeacherMiniSerializer(read_only=True)
    schedule = SerializerMethodField()
    room = SerializerMethodField()
    total_lessons_held = SerializerMethodField()
    current_lesson_number = SerializerMethodField()
    next_lesson = SerializerMethodField()
    attendance_rate = SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "status",
            "course",
            "teacher",
            "room",
            "schedule",
            "start_date",
            "end_date",
            "total_lessons_held",
            "current_lesson_number",
            "next_lesson",
            "attendance_rate",
        ]

    def get_schedule(self, group):
        return ScheduleSerializer(group).data

    def get_room(self, group):
        if not group.room_id:
            return None
        return {"id": group.room_id, "name": group.room.name}

    def _lessons_qs(self, group):
        return Lesson.objects.filter(group=group).order_by("date", "start_time")

    def get_total_lessons_held(self, group):
        return self._lessons_qs(group).filter(date__lte=timezone.now().date()).count()

    def get_current_lesson_number(self, group):
        today = timezone.now().date()
        held = self._lessons_qs(group).filter(date__lte=today).count()
        has_upcoming = self._lessons_qs(group).filter(date__gte=today).exists()
        return held + 1 if has_upcoming else held

    def get_next_lesson(self, group):
        lesson = self._lessons_qs(group).filter(date__gte=timezone.now().date()).first()
        if not lesson:
            return None
        return {
            "id": lesson.id,
            "date": lesson.date,
            "start_time": lesson.start_time.strftime("%H:%M"),
            "end_time": lesson.end_time.strftime("%H:%M"),
            "topic": lesson.topic,
        }

    def get_attendance_rate(self, group):
        student = self.context.get("student")
        if student is None:
            return None
        qs = Attendance.objects.filter(lesson__group=group, student=student)
        total = qs.count()
        if not total:
            return None
        present = qs.filter(status=Attendance.Status.PRESENT).count()
        return round(present / total * 100, 1)


class StudentAttendanceSerializer(ModelSerializer):
    lesson_date = DateField(source="lesson.date", read_only=True)
    group_id = UUIDField(source="lesson.group_id", read_only=True)
    group_name = CharField(source="lesson.group.name", read_only=True)
    topic = CharField(source="lesson.topic", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "lesson_date", "group_id", "group_name", "topic", "status", "note", "marked_at"]


class StudentDashboardSerializer(Serializer):
    id = UUIDField(read_only=True)
    full_name = CharField(read_only=True)
    phone = CharField(read_only=True)
    status = CharField(read_only=True)
    center = SerializerMethodField()
    groups = SerializerMethodField()
    attendance_summary = SerializerMethodField()

    def get_center(self, student):
        if not student.center_id:
            return None
        return {"id": student.center_id, "name": student.center.name}

    def get_groups(self, student):
        groups = (
            Group.objects.filter(enrollments__student=student, enrollments__is_active=True)
            .select_related("course", "teacher__user", "room")
            .distinct()
        )
        return StudentGroupSerializer(groups, many=True, context={"student": student}).data

    def get_attendance_summary(self, student):
        qs = Attendance.objects.filter(student=student)
        total = qs.count()
        present = qs.filter(status=Attendance.Status.PRESENT).count()
        return {
            "total_lessons": total,
            "present": present,
            "absent": total - present,
            "attendance_rate": round(present / total * 100, 1) if total else None,
        }
