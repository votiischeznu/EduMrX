import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import ImageField, EmailField, CharField, UUIDField, BooleanField, TextChoices, DateTimeField


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
    email = EmailField(blank=True, null=True)
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
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
