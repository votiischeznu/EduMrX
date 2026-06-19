from django.core.exceptions import ValidationError
from django.db.models import (
    ImageField,
    EmailField,
    CharField,
    TextChoices,
    OneToOneField,
    CASCADE,
    ForeignKey,
    SET_NULL,
    DateField,
    TextField,
    Index,
    DecimalField,
    PositiveIntegerField,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.models import TimeStampedModel
from apps.models.users import User


class Center(TimeStampedModel):
    class Plan(TextChoices):
        TRIAL = "trial", _("Trial")
        PRO = "pro", _("Pro")
        MAX = "max", _("Max")
        ENTERPRISE = "enterprise", _("Enterprise")

    class Status(TextChoices):
        ACTIVE = "active", _("Faol")
        SUSPENDED = "suspended", _("To'xtatilgan")
        INACTIVE = "inactive", _("Nofaol")

    name = CharField(_("Nomi"), max_length=255)
    slug = CharField(_("Slug"), max_length=255, unique=True)
    logo = ImageField(_("Logo"), upload_to="centers/logos/%Y/", blank=True, null=True)
    address = TextField(_("Manzil"), blank=True)
    phone = CharField(_("Telefon"), max_length=50, blank=True)
    email = EmailField(_("Email"), blank=True, null=True)
    plan = CharField(_("Tarif rejasi"), max_length=20, choices=Plan.choices, default=Plan.TRIAL)
    latitude = DecimalField(_("Kenglik (Latitude)"), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = DecimalField(_("Uzunlik (Longitude)"), max_digits=9, decimal_places=6, null=True, blank=True)
    director = ForeignKey(
        "apps.User",
        SET_NULL,
        null=True,
        blank=True,
        related_name="directed_centers",
        limit_choices_to={"role": User.Role.DIRECTOR},
        verbose_name=_("Direktor"),
    )
    status = CharField(_("Holat"), max_length=20, choices=Status.choices, default=Status.ACTIVE)
    subscription_expires = DateField(_("Tarif tugash sanasi"), null=True, blank=True)

    total_groups = PositiveIntegerField(default=0, editable=False)
    total_students = PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["name"]
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
    user = OneToOneField("apps.User", CASCADE, related_name="staff_profile", limit_choices_to={"role": User.Role.ADMIN})
    center = ForeignKey("apps.Center", CASCADE, related_name="staff_members")
    notes = TextField(_("Izoh"), blank=True)

    def __str__(self) -> str:
        return f"{self.user.full_name} — {self.center.name}"

    def clean(self):
        if self.user.role != User.Role.ADMIN:
            raise ValidationError(_("Faqat ADMIN rolidagi foydalanuvchi xodim bo'la oladi"))
