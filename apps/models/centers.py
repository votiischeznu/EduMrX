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
    slug = CharField(_("Slug"), max_length=255, unique=True) # TODO backend ozida name orqali olish
    logo = ImageField(_("Logo"), upload_to="centers/logos/%Y/", blank=True, null=True)
    address = TextField(_("Manzil"), blank=True)
    phone = CharField(_("Telefon"), max_length=50, blank=True)
    email = EmailField(_("Email"), blank=True, null=True)
    branch_limit = PositiveIntegerField(
        _("Filiallar limiti"),
        null=True,
        blank=True,
        help_text=_("Bo'sh (null) bo'lsa — tarif rejasiga qarab standart limit qo'llaniladi."),
    )
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
    PLAN_DEFAULT_BRANCH_LIMITS = {
        Plan.TRIAL: 1,
        Plan.PRO: 3,
        Plan.MAX: 10,
        Plan.ENTERPRISE: None,
    }

    class Meta:
        ordering = ["name"]
        indexes = [Index(fields=["status"]), Index(fields=["slug"])]

    def __str__(self) -> str:
        return self.name

    @property
    def effective_branch_limit(self):
        if self.branch_limit is not None:
            return self.branch_limit
        return self.PLAN_DEFAULT_BRANCH_LIMITS.get(self.plan)

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
    branch = ForeignKey("apps.Branch", SET_NULL, null=True, blank=True)
    notes = TextField(_("Izoh"), blank=True)

    def __str__(self) -> str:
        return f"{self.user.full_name} — {self.center.name}"

    def clean(self):
        if self.user.role != User.Role.ADMIN: # TODO togrilash kk
            raise ValidationError(_("Faqat ADMIN rolidagi foydalanuvchi xodim bo'la oladi"))


class Branch(TimeStampedModel):
    class Status(TextChoices):
        ACTIVE = "active", _("Faol")
        FROZEN = "frozen", _("Muzlatilgan")
        ARCHIVED = "archived", _("Arxivlangan")

    center = ForeignKey("apps.Center", CASCADE, related_name="branches", verbose_name=_("O'quv markazi"))

    manager = OneToOneField(
        "apps.User",
        SET_NULL,
        null=True,
        blank=True,
        related_name="managed_branch",
        limit_choices_to={"role": User.Role.ADMIN},
        verbose_name=_("Filial boshlig'i"),
    )

    name = CharField(_("Nomi"), max_length=255)
    address = TextField(_("Manzil"))
    phone = CharField(_("Telefon"), max_length=50)

    latitude = DecimalField(_("Kenglik"), max_digits=9, decimal_places=6)
    longitude = DecimalField(_("Uzunlik"), max_digits=9, decimal_places=6)

    status = CharField(_("Holat"), max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-created_at"]
        indexes = [Index(fields=["status"]), Index(fields=["center"])]

    def __str__(self):
        return f"{self.name} — {self.center.name}"

    @property
    def coordinates(self):
        return [float(self.latitude), float(self.longitude)]

    @property
    def active_students_count(self) -> int:
        return self.students.filter(user__is_deleted=False).count()

    @property
    def teachers_count(self) -> int:
        return self.teachers.filter(user__is_deleted=False).count()

    @property
    def rooms_count(self) -> int:
        return self.rooms.count()
