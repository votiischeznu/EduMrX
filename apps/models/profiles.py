from django.core.exceptions import ValidationError
from django.db.models import (
    CharField,
    TextChoices,
    OneToOneField,
    CASCADE,
    ForeignKey,
    SET_NULL,
    DateField,
    TextField,
    PositiveSmallIntegerField,
    DecimalField,
    Index,
    QuerySet,
    F,
)
from django.utils.translation import gettext_lazy as _

from apps.models.users import TimeStampedModel
from apps.models.users import User


class Teacher(TimeStampedModel):
    user = OneToOneField(
        "apps.User",
        CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    centers = ForeignKey(
        "apps.Center", CASCADE, related_name="teachers", null=True, blank=True
    )

    specialization = CharField(_("Mutaxassislik"), max_length=255, blank=True)
    experience = PositiveSmallIntegerField(_("Tajriba (yil)"), default=0)
    salary = DecimalField(
        _("Maosh"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    bio = TextField(_("Bio"), blank=True)
    date_of_birth = DateField(_("Tug'ilgan sana"), null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.user.full_name

    def clean(self):
        if self.user.role != User.Role.TEACHER:
            raise ValidationError(
                _("Faqat TEACHER rolidagi foydalanuvchi o'qituvchi bo'la oladi")
            )

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def phone(self) -> str:
        return self.user.phone


class Parent(TimeStampedModel):
    user = OneToOneField(
        User,
        CASCADE,
        related_name="parent_profile",
        limit_choices_to={"role": User.Role.PARENT},
    )
    address = TextField(_("Manzil"), blank=True)
    notes = TextField(_("Izoh"), blank=True)
    occupation = CharField(_("Kasbi"), max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.user.full_name

    def clean(self):
        if self.user.role != User.Role.PARENT:
            raise ValidationError(
                _("Faqat PARENT rolidagi foydalanuvchi ota-ona bo'la oladi")
            )

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def phone(self) -> str:
        return self.user.phone


class StudentQuerySet(QuerySet):
    def for_user(self, user):
        if user.is_anonymous:
            return self.none()
        if user.role == User.Role.SUPER_ADMIN:
            return self.all()
        if user.role == User.Role.DIRECTOR:
            return self.filter(center__director=user)
        if user.role == User.Role.ADMIN:
            return self.filter(center=user.center)
        if user.role == User.Role.TEACHER:
            return self.filter(enrollments__group__teacher__user=user).distinct()
        return self.none()


class Student(TimeStampedModel):
    class Status(TextChoices):
        ACTIVE = "active", _("Faol")
        INACTIVE = "inactive", _("Nofaol")
        FROZEN = "frozen", _("Muzlatilgan")
        NEW = "new", _("Yangi")
        GRADUATED = "graduated", _("Bitirgan")
        SUSPENDED = "suspended", _("To'xtatilgan")

    @property
    def is_chargeable(self) -> bool:
        return self.status in [self.Status.ACTIVE, self.Status.NEW]

    @property
    def is_first_lesson_free(self) -> bool:
        return self.status == self.Status.NEW

    user = OneToOneField(
        "apps.User",
        CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    center = ForeignKey(
        "apps.Center",
        CASCADE,
        related_name="students",
        verbose_name=_("O'quv markazi"),
    )
    parent = ForeignKey(
        "apps.Parent",
        SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Ota-ona"),
    )
    date_of_birth = DateField(_("Tug'ilgan sana"), null=True, blank=True)
    notes = TextField(_("Izoh"), blank=True)
    status = CharField(
        _("Holat"), max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    enrolled_at = DateField(_("Ro'yxatga olingan sana"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["status"]),
            Index(fields=["center"]),
            Index(fields=["-created_at"]),
            Index(fields=["center", "status"]),
        ]

    def __str__(self) -> str:
        return self.user.full_name

    objects = StudentQuerySet.as_manager()

    def save(self, *args, **kwargs):
        from apps.models.centers import Center

        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and self.center_id:
            Center.objects.filter(id=self.center_id).update(
                total_students=F("total_students") + 1
            )

    def delete(self, *args, **kwargs):
        from apps.models.centers import Center

        center_id = self.center_id
        super().delete(*args, **kwargs)

        if center_id:
            Center.objects.filter(id=center_id).update(
                total_students=F("total_students") - 1
            )

    def clean(self):
        if self.user.role != User.Role.STUDENT:
            raise ValidationError(
                _("Faqat STUDENT rolidagi foydalanuvchi talaba bo'la oladi")
            )

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def phone(self) -> str:
        return self.user.phone

    @property
    def email(self) -> str | None:
        return self.user.email
