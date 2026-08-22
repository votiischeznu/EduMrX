import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models import (
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    EmailField,
    Index,
    TextChoices,
    URLField,
    UUIDField, ImageField,
)

from django.utils.translation import gettext_lazy as _

from apps.models.manager import AllUserManager, UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(TextChoices):
        SUPER_ADMIN = "super_admin", _("Super Admin")
        DIRECTOR = "director", _("Direktor")
        ADMIN = "admin", _("Admin (Reception)")
        TEACHER = "teacher", _("O'qituvchi")
        STUDENT = "student", _("Talaba")
        PARENT = "parent", _("Ota-ona")

    class Gender(TextChoices):
        MALE = "male", _("Erkak")
        FEMALE = "female", _("Ayol")

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gender = CharField(_("Jinsi"), max_length=10, choices=Gender.choices, null=True, blank=True)
    phone = CharField(_("Telefon"), max_length=50, unique=True)
    email = EmailField(_("Email"), blank=True, null=True, unique=True)
    backup_phone = CharField(_("Qo'shimcha telefon"), max_length=30, blank=True, null=True, unique=True)
    first_name = CharField(_("Ism"), max_length=100)
    last_name = CharField(_("Familiya"), max_length=100)
    role = CharField(_("Rol"), max_length=20, choices=Role.choices, default=Role.STUDENT)
    avatar = ImageField(_("Rasm"),upload_to="avatars/", blank=True, null=True)
    is_deleted = BooleanField(default=False)
    telegram_id = BigIntegerField(
        _("Telegram ID"),
        unique=True,
        null=True,
        blank=True,
        help_text=_("Foydalanuvchining Telegram chat/user ID raqami"),
    )
    telegram_username = CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name=_("Telegram username"),
    )
    telegram_linked_at = DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Telegram bog'langan vaqti"),
    )
    is_active = BooleanField(_("Faol"), default=True)
    is_staff = BooleanField(_("Xodim"), default=False)
    must_change_password = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    objects = UserManager()
    all_objects = AllUserManager()

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

    def soft_delete(self):
        """
        Userni o'chiradi (is_deleted=True) va shu bilan birga unique
        maydonlarni (phone/email/backup_phone) darhol bo'shatadi.

        Nega bu muhim: agar faqat is_deleted=True qilib qo'ysak-u,
        phone maydonini o'zgartirmasak, DB darajasidagi unique
        constraint tufayli boshqa hech kim shu raqam bilan ro'yxatdan
        o'tolmaydi — hatto User.objects (filtrlangan manager) bu
        o'chirilgan yozuvni "ko'rmasa" ham. Constraint Python filteriga
        emas, DB'ning o'ziga bog'liq.
        """
        if self.phone and "_deleted_" not in self.phone:
            self.phone = f"{self.phone}_deleted_{self.id.hex[:8]}"
        if self.email and "_deleted_" not in self.email:
            self.email = f"{self.email}.deleted.{self.id.hex[:8]}"
        if self.backup_phone and "_deleted_" not in self.backup_phone:
            self.backup_phone = f"{self.backup_phone}_deleted_{self.id.hex[:8]}"

        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["phone", "email", "backup_phone", "is_deleted", "is_active"])
