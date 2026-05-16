import uuid

from django.db.models import PROTECT, DateField, CharField, UUIDField, BooleanField, TextChoices, DateTimeField, \
    Model, IntegerChoices, CASCADE, ForeignKey, PositiveSmallIntegerField, ManyToManyField, TimeField, JSONField

from apps.models.courses import Course
from apps.models.students import Student
from apps.models.users import User


class Group(Model):
    class Status(TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    class DayOfWeek(IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(max_length=200)
    course = ForeignKey(Course, on_delete=PROTECT, related_name="groups")
    teacher = ForeignKey(
        User,
        on_delete=PROTECT,
        related_name="teaching_groups",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    students = ManyToManyField(Student, through="GroupStudent", related_name="groups", blank=True)

    max_students = PositiveSmallIntegerField(default=20)
    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    start_date = DateField()
    end_date = DateField(null=True, blank=True)

    # Class schedule
    lesson_days = JSONField(
        default=list,
        help_text="List of day integers (0=Monday ... 6=Sunday)"
    )
    lesson_start_time = TimeField()
    lesson_end_time = TimeField()
    room = CharField(max_length=100, blank=True)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        db_table = "groups"
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.course.name}"

    @property
    def student_count(self):
        return self.students.count()

    @property
    def is_full(self):
        return self.student_count >= self.max_students


class GroupStudent(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = ForeignKey(Group, on_delete=CASCADE, related_name="enrollments")
    student = ForeignKey(Student, on_delete=CASCADE, related_name="enrollments")
    joined_at = DateField(auto_now_add=True)
    is_active = BooleanField(default=True)

    class Meta:
        db_table = "group_students"
        verbose_name = "Group Student"
        verbose_name_plural = "Group Students"
        unique_together = ("group", "student")

    def __str__(self):
        return f"{self.student} → {self.group}"
