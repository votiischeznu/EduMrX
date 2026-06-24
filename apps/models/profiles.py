from django.core.exceptions import ValidationError
from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateField,
    DecimalField,
    F,
    ForeignKey,
    Index,
    OneToOneField,
    PositiveSmallIntegerField,
    QuerySet,
    TextChoices,
    TextField,
)
from django.utils.translation import gettext_lazy as _

from apps.models import TimeStampedModel
from apps.models.users import User


class Teacher(TimeStampedModel):
    user = OneToOneField(
        "apps.User", CASCADE, related_name="teacher_profile", limit_choices_to={"role": User.Role.TEACHER}
    )
    centers = ForeignKey("apps.Center", CASCADE, related_name="teachers", null=True, blank=True)
    branch = ForeignKey(
        "apps.Branch", SET_NULL, null=True, blank=True, related_name="teachers", verbose_name=_("Filial")
    )
    specialization = CharField(_("Mutaxassislik"), max_length=255, blank=True)
    experience = PositiveSmallIntegerField(_("Tajriba (yil)"), default=0)
    salary = DecimalField(_("Maosh"), max_digits=12, decimal_places=2, null=True, blank=True)
    bio = TextField(_("Bio"), blank=True)
    date_of_birth = DateField(_("Tug'ilgan sana"), null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.full_name

    def clean(self):
        if self.user and not self.user.is_teacher:  # TODO is bilan property ✅
            raise ValidationError(_("Faqat TEACHER rolidagi foydalanuvchi o'qituvchi bo'la oladi"))

    def delete(self, *args, **kwargs):
        if self.teaching_groups.exists():
            raise ValidationError(
                _(
                    "Bu o'qituvchini o'chirish mumkin emas: unga bog'langan guruhlar mavjud. "
                    "Avval guruhlarni boshqa o'qituvchiga o'tkazing yoki arxivlang."
                )
            )
        super().delete(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def phone(self) -> str:
        return self.user.phone


class Parent(TimeStampedModel):
    user = OneToOneField(
        "apps.User", CASCADE, related_name="parent_profile", limit_choices_to={"role": User.Role.PARENT}
    )  # TODO apps. deb yozish ✅
    address = TextField(_("Manzil"), blank=True)
    notes = TextField(_("Izoh"), blank=True)
    occupation = CharField(_("Kasbi"), max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.user.full_name

    def clean(self):
        if self.user and not self.user.is_parent:
            raise ValidationError(_("Faqat PARENT rolidagi foydalanuvchi ota-ona bo'la oladi"))

    def delete(self, *args, **kwargs):
        if self.children.exists():
            raise ValidationError(
                _(
                    "Bu ota-onani o'chirish mumkin emas: unga bog'langan farzandlar mavjud. "
                    "Avval farzandlarni boshqa ota-onaga bog'lang yoki bog'lanishni uzing."
                )
            )
        super().delete(*args, **kwargs)

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
        if user.is_super_admin:
            return self.all()
        if user.is_director:
            return self.filter(center__director=user)
        if user.is_admin:
            staff_profile = getattr(user, "staff_profile", None)
            if staff_profile is None:
                return self.none()
            return self.filter(center=staff_profile.center)
        if user.is_teacher:
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

    user = OneToOneField(
        "apps.User", CASCADE, related_name="student_profile", limit_choices_to={"role": User.Role.STUDENT}
    )
    center = ForeignKey("apps.Center", CASCADE, related_name="students", verbose_name=_("O'quv markazi"))
    branch = ForeignKey(
        "apps.Branch", SET_NULL, null=True, blank=True, related_name="students", verbose_name=_("Filial")
    )
    parent = ForeignKey(
        "apps.Parent", SET_NULL, null=True, blank=True, related_name="children", verbose_name=_("Ota-ona")
    )
    date_of_birth = DateField(_("Tug'ilgan sana"), null=True, blank=True)
    notes = TextField(_("Izoh"), blank=True)
    status = CharField(_("Holat"), max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = DateField(_("Ro'yxatga olingan sana"), auto_now_add=True)

    objects = StudentQuerySet.as_manager()

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

    @property
    def is_chargeable(self) -> bool:
        return self.status in [self.Status.ACTIVE, self.Status.NEW]

    @property
    def is_first_lesson_free(self) -> bool:
        return self.status == self.Status.NEW

    def save(self, *args, **kwargs):
        from apps.models.centers import Center

        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and self.center_id:
            Center.objects.filter(id=self.center_id).update(total_students=F("total_students") + 1)

    def delete(self, *args, **kwargs):
        from apps.models.centers import Center

        center_id = self.center_id
        super().delete(*args, **kwargs)

        if center_id:
            Center.objects.filter(id=center_id).update(total_students=F("total_students") - 1)

    def clean(self):
        if self.user and not self.user.is_student:
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
