import uuid

from django.core.exceptions import ValidationError
from django.db.models import (
    ImageField, EmailField, CharField, UUIDField, TextChoices, OneToOneField, CASCADE,
    ForeignKey, SET_NULL, DateField, TextField, Index, )
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.models.users import User
from apps.models.users import TimeStampedModel


class Center(TimeStampedModel):
    class Status(TextChoices):
        ACTIVE = "active", _("Faol")
        SUSPENDED = "suspended", _("To'xtatilgan")
        INACTIVE = "inactive", _("Nofaol")

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(_("Nomi"), max_length=255)
    slug = CharField(_("Slug"), max_length=255, unique=True)
    logo = ImageField(_("Logo"), upload_to="centers/logos/%Y/", blank=True, null=True)
    address = TextField(_("Manzil"), blank=True)
    phone = CharField(_("Telefon"), max_length=20, blank=True)
    email = EmailField(_("Email"), blank=True, null=True)

    director = ForeignKey(
        'apps.User',
        on_delete=SET_NULL,
        null=True, blank=True,
        related_name="directed_centers",
        limit_choices_to={"role": User.Role.DIRECTOR},
        verbose_name=_("Direktor"),
    )

    status = CharField(_("Holat"), max_length=20, choices=Status.choices, default=Status.ACTIVE)
    subscription_expires = DateField(_("Tarif tugash sanasi"), null=True, blank=True)

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
        'apps.User', on_delete=CASCADE,
        related_name="staff_profile",
        limit_choices_to={"role": User.Role.ADMIN},
    )
    center = ForeignKey(
        'apps.Center', on_delete=CASCADE,
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
