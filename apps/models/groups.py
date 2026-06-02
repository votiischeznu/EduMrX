import uuid

from django.db.models import PROTECT, DateField, CharField, UUIDField, BooleanField, TextChoices, Model, IntegerChoices, \
    CASCADE, ForeignKey, PositiveSmallIntegerField, ManyToManyField, TimeField, JSONField, \
    SET_NULL

from apps.models.users import TimeStampedModel


class Room(TimeStampedModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(max_length=100)
    capacity = PositiveSmallIntegerField()

    class Meta:
        db_table = "rooms"
        verbose_name = "Room"
        verbose_name_plural = "Rooms"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.capacity} seats)"


class Group(TimeStampedModel):
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
    course = ForeignKey('apps.Course', PROTECT, related_name="groups")
    teacher = ForeignKey('apps.Teacher', PROTECT, related_name="teaching_groups")
    students = ManyToManyField('apps.Student', through="GroupStudent", related_name="groups", blank=True)

    room = ForeignKey(
        'apps.Room',
        SET_NULL,     null=True, blank=True,
        related_name="groups"
    )
    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    center = ForeignKey('apps.Center', CASCADE, related_name="groups", null=True, blank=True)

    start_date = DateField()
    end_date = DateField(null=True, blank=True)

    lesson_days = JSONField(
        default=list,
        help_text="List of week day integers (0=Monday ... 6=Sunday)"
    )
    lesson_start_time = TimeField()
    lesson_end_time = TimeField()

    class Meta:
        db_table = "groups"
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.course.name}"

    def clean(self):
        errors = {}
        valid_days = [day.value for day in self.DayOfWeek]

        if not isinstance(self.lesson_days, list):
            errors["lesson_days"] = "Lesson days must be a list"

        else:
            for day in self.lesson_days:
                if day not in valid_days:
                    errors["lesson_days"] = (
                        "Lesson days must contain values from 0 to 6 only"
                    )

            if len(self.lesson_days) != len(set(self.lesson_days)):
                errors["lesson_days"] = (
                    "Duplicate lesson days are not allowed"
                )

    @property
    def student_count(self):
        return self.students.count()

    @property
    def capacity(self):
        return self.room.capacity if self.room_id else None

    @property
    def is_full(self):
        if self.capacity is None:
            return False
        return self.student_count >= self.capacity


class GroupStudent(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = ForeignKey('apps.Group', on_delete=CASCADE, related_name="enrollments")
    student = ForeignKey('apps.Student', on_delete=CASCADE, related_name="enrollments")
    joined_at = DateField(auto_now_add=True)
    is_active = BooleanField(default=True)

    class Meta:
        unique_together = ("group", "student")

    def __str__(self):
        return f"{self.student} → {self.group}"
