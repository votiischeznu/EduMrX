import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import (
    ImageField, EmailField, CharField, UUIDField, BooleanField,
    TextChoices, DateTimeField, Model, OneToOneField, CASCADE, ForeignKey, SET_NULL, DateField, TextField
)


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(TextChoices):
        ADMIN = "admin", "Admin"
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"
        PARENT = "parent", "Parent"

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = CharField(max_length=20, unique=True)
    email = EmailField(blank=True, null=True, unique=True)
    backup_phone = CharField(max_length=20, blank=True, null=True, unique=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    role = CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    avatar = ImageField(upload_to="avatars/", blank=True, null=True)

    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


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
