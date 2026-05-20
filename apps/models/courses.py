import uuid

from django.db.models import TextField, CharField, UUIDField, TextChoices, DateTimeField, \
    Model, PositiveSmallIntegerField, DecimalField, CASCADE, ForeignKey, DateField, TimeField


class Course(Model):
    class Status(TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(max_length=200)
    description = TextField(blank=True)
    duration_months = PositiveSmallIntegerField(default=1)
    price = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Lesson(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = ForeignKey('apps.Group', on_delete=CASCADE, related_name="lessons")
    date = DateField()
    start_time = TimeField()
    end_time = TimeField()
    topic = CharField(max_length=300, blank=True)
    notes = TextField(blank=True)

    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lessons"
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ["-date", "-start_time"]
        unique_together = ("group", "date", "start_time")

    def __str__(self):
        return f"{self.group.name} | {self.date}"


class Attendance(Model):
    class Status(TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = ForeignKey('apps.Lesson', on_delete=CASCADE, related_name="attendances")
    student = ForeignKey('apps.Student', on_delete=CASCADE, related_name="attendances")
    status = CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    note = CharField(max_length=300, blank=True)

    marked_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("lesson", "student")
        ordering = ["-lesson__date"]

    def __str__(self):
        return f"{self.student} | {self.lesson.date} | {self.status}"
