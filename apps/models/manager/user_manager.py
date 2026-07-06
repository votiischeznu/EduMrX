from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)


class UserManager(BaseUserManager):
    """
    Default manager.

    get_queryset() faqat is_deleted=False bo'lgan userlarni qaytaradi.
    Shu tufayli User.objects.filter(...) to'g'ridan-to'g'ri chaqirilgan
    HAR QANDAY joy (login, register, recovery, director create, contact
    signal) avtomatik ravishda o'chirilgan userlarni e'tiborsiz qoldiradi.

    DIQQAT: bu Student.objects.filter(user__is_deleted=False) kabi
    related-lookup (JOIN) filtrlarga ta'sir qilmaydi — ular alohida,
    to'g'ridan-to'g'ri SQL darajasida ishlaydi va har doim kerak bo'lib
    qoladi. Bu manager faqat User.objects orqali TO'G'RIDAN-TO'G'RI
    ishlatilgan joylarni qamrab oladi.

    O'chirilganlarni ham ko'rish kerak bo'lsa (admin panel, audit),
    User.all_objects dan foydalaning.
    """

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db).active()

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
        extra_fields.setdefault("role", self.model.Role.STUDENT)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", self.model.Role.SUPER_ADMIN)  # TODO universal ✅
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser uchun is_staff=True bo'lishi shart"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser uchun is_superuser=True bo'lishi shart"))
        return self._create_user(phone, password, **extra_fields)


class AllUserManager(BaseUserManager):
    """
    O'chirilganlarni ham ko'rsatadigan manager.
    FAQAT admin panel / audit / support uchun ishlatilishi kerak.
    """

    def get_queryset(self):
        return models.QuerySet(self.model, using=self._db)