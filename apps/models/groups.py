from django.core.exceptions import ValidationError
from django.db.models import (
    PROTECT,
    DateField,
    CharField,
    BooleanField,
    TextChoices,
    IntegerChoices,
    CASCADE,
    ForeignKey,
    PositiveSmallIntegerField,
    ManyToManyField,
    TimeField,
    JSONField,
    SET_NULL,
    F,
)

from apps.models import BaseModel, TimeStampedModel


class Room(TimeStampedModel):
    center = ForeignKey("apps.Center", CASCADE, related_name="rooms")
    branch = ForeignKey("apps.Branch", SET_NULL, null=True, blank=True, related_name="rooms")
    name = CharField(max_length=100)
    capacity = PositiveSmallIntegerField()

    class Meta:
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

    name = CharField(max_length=200)
    course = ForeignKey("apps.Course", PROTECT, related_name="groups")
    teacher = ForeignKey("apps.Teacher", PROTECT, related_name="teaching_groups")
    students = ManyToManyField("apps.Student", through="GroupStudent", related_name="groups", blank=True)
    student_count = PositiveSmallIntegerField(default=0, editable=False)
    room = ForeignKey("apps.Room", SET_NULL, null=True, blank=True, related_name="groups")
    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    center = ForeignKey("apps.Center", CASCADE, related_name="groups", null=True, blank=True)
    branch = ForeignKey("apps.Branch", SET_NULL, null=True, blank=True, related_name="groups")

    start_date = DateField()
    end_date = DateField(null=True, blank=True)

    lesson_days = JSONField(default=list, help_text="List of week day integers (0=Monday ... 6=Sunday)")
    lesson_start_time = TimeField()
    lesson_end_time = TimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.course.name}"

    def save(self, *args, **kwargs):
        from apps.models.centers import Center

        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and self.center_id:
            Center.objects.filter(id=self.center_id).update(total_groups=F("total_groups") + 1)

    def delete(self, *args, **kwargs):
        from apps.models.centers import Center

        center_id = self.center_id
        super().delete(*args, **kwargs)

        if center_id:
            Center.objects.filter(id=center_id).update(total_groups=F("total_groups") - 1)

    def clean(self):
        super().clean()
        errors = {}
        valid_days = [day.value for day in self.DayOfWeek]

        if not isinstance(self.lesson_days, list):
            errors["lesson_days"] = "Lesson days must be a list"
        else:
            for day in self.lesson_days:
                if day not in valid_days:
                    errors["lesson_days"] = "Lesson days must contain values from 0 to 6 only"
                    break

            if len(self.lesson_days) != len(set(self.lesson_days)):
                errors["lesson_days"] = "Duplicate lesson days are not allowed"

        if errors:
            raise ValidationError(errors)

    @property
    def capacity(self):
        return self.room.capacity if self.room_id else None

    @property
    def is_full(self):
        if self.capacity is None:
            return False
        return self.student_count >= self.capacity


class GroupStudent(BaseModel):
    group = ForeignKey("apps.Group", CASCADE, related_name="enrollments")
    student = ForeignKey("apps.Student", CASCADE, related_name="enrollments")
    joined_at = DateField(auto_now_add=True)
    is_active = BooleanField(default=True)

    class Meta:
        unique_together = (("group", "student"),)

    def __str__(self):
        return f"{self.student} → {self.group}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            Group.objects.filter(id=self.group_id).update(student_count=F("student_count") + 1)

    def delete(self, *args, **kwargs):
        group_id = self.group_id
        super().delete(*args, **kwargs)
        Group.objects.filter(id=group_id).update(student_count=F("student_count") - 1)
