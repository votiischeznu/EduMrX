import random
import uuid
from datetime import timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db.models import (
    ImageField, EmailField, CharField, UUIDField, BooleanField,
    TextChoices, DateTimeField, Model, ForeignKey, CASCADE
)
from django.utils.timezone import now


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


class AccountRecovery(Model):
    class Method(TextChoices):
        BACKUP_PHONE = "backup_phone", "Backup Phone"
        EMAIL = "email", "Email"

    class Status(TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = ForeignKey(User, on_delete=CASCADE, related_name="recovery_requests")

    method = CharField(max_length=20, choices=Method.choices)
    new_phone = CharField(max_length=20)

    otp_code = CharField(max_length=128, blank=True)
    otp_expires_at = DateTimeField(null=True, blank=True)

    status = CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        db_table = "account_recoveries"
        verbose_name = "Account Recovery"
        verbose_name_plural = "Account Recoveries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} | {self.method} | {self.status}"

    def set_otp(self, raw_otp: str):
        self.otp_code = make_password(raw_otp)

    def verify_otp(self, raw_otp: str) -> bool:
        return check_password(raw_otp, self.otp_code)


class AccountRecoveryService:

    @staticmethod
    def start(user: User, new_phone: str, method: str) -> AccountRecovery:
        AccountRecovery.objects.filter(
            user=user,
            status=AccountRecovery.Status.PENDING
        ).update(status=AccountRecovery.Status.CANCELLED)

        if User.objects.filter(phone=new_phone).exists():
            raise ValidationError("Bu telefon raqam allaqachon ishlatilmoqda")

        if method == AccountRecovery.Method.EMAIL and not user.email:
            raise ValidationError("Email manzilingiz mavjud emas")
        if method == AccountRecovery.Method.BACKUP_PHONE and not user.backup_phone:
            raise ValidationError("Zaxira telefon raqamingiz mavjud emas")

        otp = str(random.randint(100000, 999999))

        recovery = AccountRecovery(
            user=user,
            new_phone=new_phone,
            method=method,
            otp_expires_at=now() + timedelta(minutes=10),
        )
        recovery.set_otp(otp)
        recovery.save()

        if method == AccountRecovery.Method.EMAIL:
            AccountRecoveryService._send_email(user.email, otp)
        else:
            AccountRecoveryService._send_sms(user.backup_phone, otp)

        return recovery

    @staticmethod
    def verify(recovery: AccountRecovery, raw_otp: str) -> AccountRecovery:
        if recovery.status != AccountRecovery.Status.PENDING:
            raise ValidationError("Bu so'rov allaqachon ishlatilgan yoki bekor qilingan")

        if now() > recovery.otp_expires_at:
            recovery.status = AccountRecovery.Status.EXPIRED
            recovery.save(update_fields=["status", "updated_at"])
            raise ValidationError("OTP muddati o'tgan, qaytadan boshlang")

        if not recovery.verify_otp(raw_otp):
            raise ValidationError("OTP kod xato")

        recovery.status = AccountRecovery.Status.VERIFIED
        recovery.save(update_fields=["status", "updated_at"])
        return recovery

    @staticmethod
    def complete(recovery: AccountRecovery, new_password: str) -> User:
        if recovery.status != AccountRecovery.Status.VERIFIED:
            raise ValidationError("OTP hali tasdiqlanmagan")

        user = recovery.user
        user.phone = recovery.new_phone
        user.set_password(new_password)
        user.save(update_fields=["phone", "password", "updated_at"])

        recovery.status = AccountRecovery.Status.COMPLETED
        recovery.save(update_fields=["status", "updated_at"])

        return user

    @staticmethod
    def _send_sms(phone: str, otp: str):
        pass

    @staticmethod
    def _send_email(email: str, otp: str):
        pass