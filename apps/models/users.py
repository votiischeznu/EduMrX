from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db.models import (
    EmailField,
    CharField,
    BooleanField,
    TextChoices,
    Index,
    URLField,
)
from django.utils.translation import gettext_lazy as _

from apps.models.base_models import TimeStampedModel


class UserManager(BaseUserManager):
    def _create_user(self, phone: str, password: str | None, **extra_fields):
        if not phone:
            raise ValueError(_("Telefon raqam majburiy"))
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.STUDENT)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser uchun is_staff=True bo'lishi shart"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser uchun is_superuser=True bo'lishi shart"))

        return self._create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    class Role(TextChoices):
        SUPER_ADMIN = "super_admin", _("Super Admin")
        DIRECTOR = "director", _("Direktor")
        ADMIN = "admin", _("Admin (Reception)")
        TEACHER = "teacher", _("O'qituvchi")
        STUDENT = "student", _("Talaba")
        PARENT = "parent", _("Ota-ona")

    phone = CharField(_("Telefon"), max_length=50, unique=True)
    email = EmailField(_("Email"), blank=True, null=True, unique=True)
    backup_phone = CharField(
        _("Qo'shimcha telefon"), max_length=30, blank=True, null=True, unique=True
    )
    first_name = CharField(_("Ism"), max_length=100)
    last_name = CharField(_("Familiya"), max_length=100)
    role = CharField(
        _("Rol"), max_length=20, choices=Role.choices, default=Role.STUDENT
    )
    avatar = URLField(_("Rasm"), blank=True, null=True)
    is_deleted = BooleanField(default=False)

    is_active = BooleanField(_("Faol"), default=True)
    is_staff = BooleanField(_("Xodim"), default=False)

    must_change_password = BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["role"]),
            Index(fields=["is_active"]),
            Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_super_admin(self) -> bool:
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_director(self) -> bool:
        return self.role == self.Role.DIRECTOR

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_teacher(self) -> bool:
        return self.role == self.Role.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_parent(self) -> bool:
        return self.role == self.Role.PARENT
