import uuid

from django.db.models import PROTECT, DateField, CharField, UUIDField, BooleanField, TextChoices, DateTimeField, \
    Model, IntegerChoices, CASCADE, ForeignKey, PositiveSmallIntegerField, ManyToManyField, TimeField, JSONField, \
    SET_NULL

from apps.models.users import User


class Room(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(max_length=100)
    capacity = PositiveSmallIntegerField()

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        db_table = "rooms"
        verbose_name = "Room"
        verbose_name_plural = "Rooms"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.capacity} seats)"


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
    course = ForeignKey('apps.Course', on_delete=PROTECT, related_name="groups")
    teacher = ForeignKey(
        'apps.User',
        on_delete=PROTECT,
        related_name="teaching_groups",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    students = ManyToManyField('apps.Student', through="GroupStudent", related_name="groups", blank=True)

    room = ForeignKey(
        'apps.Room',
        on_delete=SET_NULL,
        null=True, blank=True,
        related_name="groups"
    )

    max_students = PositiveSmallIntegerField(null=True, blank=True)

    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    start_date = DateField()
    end_date = DateField(null=True, blank=True)

    lesson_days = JSONField(
        default=list,
        help_text="List of day integers (0=Monday ... 6=Sunday)"
    )
    lesson_start_time = TimeField()
    lesson_end_time = TimeField()

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
    def capacity(self):
        if self.room_id:
            return self.room.capacity
        return self.max_students

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