import uuid

from django.db.models import TextField, CharField, UUIDField, TextChoices, DateTimeField, \
    Model, PositiveSmallIntegerField, DecimalField


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
        db_table = "courses"
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["name"]

    def __str__(self):
        return self.name
