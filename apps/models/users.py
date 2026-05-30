import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db.models import (
    ImageField, EmailField, CharField, UUIDField, BooleanField,
    TextChoices, DateTimeField, Model, OneToOneField, CASCADE,
    ForeignKey, SET_NULL, DateField, TextField, PositiveSmallIntegerField,
    DecimalField, Index, UniqueConstraint, Q, IntegerField,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class TimeStampedModel(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True

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


class User(AbstractBaseUser, PermissionsMixin):
    class Role(TextChoices):
        SUPER_ADMIN = "super_admin", _("Super Admin")
        DIRECTOR = "director", _("Direktor")
        ADMIN = "admin", _("Admin (Reception)")
        TEACHER = "teacher", _("O'qituvchi")
        STUDENT = "student", _("Talaba")
        PARENT = "parent", _("Ota-ona")

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = CharField(_("Telefon"), max_length=20, unique=True)
    email = EmailField(_("Email"), blank=True, null=True, unique=True)
    backup_phone = CharField(_("Qo'shimcha telefon"), max_length=20, blank=True, null=True, unique=True)
    first_name = CharField(_("Ism"), max_length=100)
    last_name = CharField(_("Familiya"), max_length=100)
    role = CharField(_("Rol"), max_length=20, choices=Role.choices, default=Role.STUDENT)
    avatar = ImageField(_("Rasm"), upload_to="avatars/%Y/%m/", blank=True, null=True)

    is_active = BooleanField(_("Faol"), default=True)
    is_staff = BooleanField(_("Xodim"), default=False)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")
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

class Center(TimeStampedModel):
    class Status(TextChoices):
        ACTIVE = "active", _("Faol")
        SUSPENDED = "suspended", _("To'xtatilgan")  # tarif to'lanmagan
        INACTIVE = "inactive", _("Nofaol")

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(_("Nomi"), max_length=255)
    slug = CharField(_("Slug"), max_length=255, unique=True)
    logo = ImageField(_("Logo"), upload_to="centers/logos/%Y/", blank=True, null=True)
    address = TextField(_("Manzil"), blank=True)
    phone = CharField(_("Telefon"), max_length=20, blank=True)
    email = EmailField(_("Email"), blank=True, null=True)

    director = ForeignKey(
        User,
        on_delete=SET_NULL,
        null=True, blank=True,
        related_name="directed_centers",
        limit_choices_to={"role": User.Role.DIRECTOR},
        verbose_name=_("Direktor"),
    )

    status = CharField(
        _("Holat"), max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    subscription_expires = DateField(
        _("Tarif tugash sanasi"),
        null=True, blank=True,
    )

    class Meta:
        db_table = "centers"
        ordering = ["name"]
        verbose_name = _("O'quv markazi")
        verbose_name_plural = _("O'quv markazlari")
        indexes = [
            Index(fields=["status"]),
            Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_subscription_active(self) -> bool:
        if self.subscription_expires is None:
            return True
        return self.subscription_expires >= timezone.now().date()

    def suspend_if_expired(self) -> bool:
        if not self.is_subscription_active and self.status == self.Status.ACTIVE:
            self.status = self.Status.SUSPENDED
            self.save(update_fields=["status", "updated_at"])
            return True
        return False

class CenterStaff(TimeStampedModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = OneToOneField(
        User, on_delete=CASCADE,
        related_name="staff_profile",
        limit_choices_to={"role": User.Role.ADMIN},
    )
    center = ForeignKey(
        Center, on_delete=CASCADE,
        related_name="staff_members",
    )
    notes = TextField(_("Izoh"), blank=True)

    class Meta:
        db_table = "center_staff"
        verbose_name = _("Markaz xodimi")
        verbose_name_plural = _("Markaz xodimlari")

    def __str__(self) -> str:
        return f"{self.user.full_name} — {self.center.name}"

    def clean(self):
        if self.user.role != User.Role.ADMIN:
            raise ValidationError(_("Faqat ADMIN rolidagi foydalanuvchi xodim bo'la oladi"))


# ─────────────────────────────────────────────
#  Teacher
# ─────────────────────────────────────────────

class Teacher(TimeStampedModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = OneToOneField(
        User, on_delete=CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    centers = ForeignKey(
        Center, on_delete=CASCADE,
        related_name="teachers",
        null=True, blank=True,
    )

    specialization = CharField(_("Mutaxassislik"), max_length=255, blank=True)
    experience = PositiveSmallIntegerField(_("Tajriba (yil)"), default=0)
    salary = DecimalField(
        _("Maosh"), max_digits=12, decimal_places=2,
        null=True, blank=True,
    )
    bio = TextField(_("Bio"), blank=True)
    date_of_birth = DateField(_("Tug'ilgan sana"), null=True, blank=True)

    class Meta:
        db_table = "teachers"
        ordering = ["-created_at"]
        verbose_name = _("O'qituvchi")
        verbose_name_plural = _("O'qituvchilar")

    def __str__(self) -> str:
        return self.user.full_name

    def clean(self):
        if self.user.role != User.Role.TEACHER:
            raise ValidationError(_("Faqat TEACHER rolidagi foydalanuvchi o'qituvchi bo'la oladi"))

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def phone(self) -> str:
        return self.user.phone

class Parent(TimeStampedModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = OneToOneField(
        User, on_delete=CASCADE,
        related_name="parent_profile",
        limit_choices_to={"role": User.Role.PARENT},
    )
    address = TextField(_("Manzil"), blank=True)
    notes = TextField(_("Izoh"), blank=True)
    occupation = CharField(_("Kasbi"), max_length=255, blank=True)

    class Meta:
        db_table = "parents"
        ordering = ["-created_at"]
        verbose_name = _("Ota-ona")
        verbose_name_plural = _("Ota-onalar")

    def __str__(self) -> str:
        return self.user.full_name

    def clean(self):
        if self.user.role != User.Role.PARENT:
            raise ValidationError(_("Faqat PARENT rolidagi foydalanuvchi ota-ona bo'la oladi"))

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def phone(self) -> str:
        return self.user.phone


class Student(TimeStampedModel):
    class Status(TextChoices):
        ACTIVE = "active", _("Faol")
        INACTIVE = "inactive", _("Nofaol")
        GRADUATED = "graduated", _("Bitirgan")
        SUSPENDED = "suspended", _("To'xtatilgan")

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = OneToOneField(
        User, on_delete=CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    center = ForeignKey(
        Center, on_delete=CASCADE,
        related_name="students",
        verbose_name=_("O'quv markazi"),
    )
    parent = ForeignKey(
        Parent,
        on_delete=SET_NULL,
        null=True, blank=True,
        related_name="children",
        verbose_name=_("Ota-ona"),
    )

    date_of_birth = DateField(_("Tug'ilgan sana"), null=True, blank=True)
    address = TextField(_("Manzil"), blank=True)
    notes = TextField(_("Izoh"), blank=True)
    status = CharField(
        _("Holat"), max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    enrolled_at = DateField(_("Ro'yxatga olingan sana"), auto_now_add=True)

    class Meta:
        db_table = "students"
        ordering = ["-created_at"]
        verbose_name = _("Talaba")
        verbose_name_plural = _("Talabalar")
        indexes = [
            Index(fields=["status"]),
            Index(fields=["center"]),
            Index(fields=["-created_at"]),
            Index(fields=["center", "status"]),  # tez-tez ishlatiladi
        ]

    def __str__(self) -> str:
        return self.user.full_name

    def clean(self):
        if self.user.role != User.Role.STUDENT:
            raise ValidationError(_("Faqat STUDENT rolidagi foydalanuvchi talaba bo'la oladi"))

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def phone(self) -> str:
        return self.user.phone

    @property
    def email(self) -> str | None:
        return self.user.email
