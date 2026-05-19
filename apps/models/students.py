import uuid

from django.db.models import TextField, DateField, CharField, UUIDField, TextChoices, DateTimeField, \
    Model, OneToOneField, CASCADE, ForeignKey, SET_NULL, EmailField


class Student(Model):
    class Status(TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        GRADUATED = "graduated", "Graduated"
        SUSPENDED = "suspended", "Suspended"

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = OneToOneField('apps.User', on_delete=CASCADE, related_name="student_profile")

    parent = ForeignKey(
        'apps.User',
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        limit_choices_to={"role": "parent"},
    )

    date_of_birth = DateField(null=True, blank=True)
    email = EmailField(blank=True, null=True)
    address = TextField(blank=True)
    notes = TextField(blank=True)
    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    enrolled_at = DateField(auto_now_add=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.full_name

    @property
    def full_name(self):
        return self.user.full_name

    @property
    def phone(self):
        return self.user.phone
