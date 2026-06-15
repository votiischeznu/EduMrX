from django.db.models import (
    TextField,
    CharField,
    TextChoices,
    PositiveSmallIntegerField,
    DecimalField,
    CASCADE,
    ForeignKey,
    DateField,
    TimeField,
    DateTimeField,
)

from apps.models import BaseModel, TimeStampedModel



class Course(TimeStampedModel):
    class Status(TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = CharField(max_length=200)
    description = TextField(blank=True)
    duration_months = PositiveSmallIntegerField(default=1)
    price = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    center = ForeignKey(
        "apps.Center",
        CASCADE,
        related_name="courses",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Lesson(TimeStampedModel):
    group = ForeignKey("apps.Group", CASCADE, related_name="lessons")
    date = DateField()
    start_time = TimeField()
    end_time = TimeField()
    topic = CharField(max_length=300, blank=True)
    notes = TextField(blank=True)

    class Meta:
        ordering = ["-date", "-start_time"]
        unique_together = ("group", "date", "start_time")

    def __str__(self):
        return f"{self.group.name} | {self.date}"


class Attendance(BaseModel):
    class Status(TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    lesson = ForeignKey("apps.Lesson", CASCADE, related_name="attendances")
    student = ForeignKey("apps.Student", CASCADE, related_name="attendances")
    status = CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    note = CharField(max_length=300, blank=True)

    marked_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("lesson", "student")
        ordering = ["-lesson__date"]

    def __str__(self):
        return f"{self.student} | {self.lesson.date} | {self.status}"
