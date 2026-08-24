from decimal import Decimal

from django.db.models import (
    PROTECT,
    SET_NULL,
    BooleanField,
    CharField,
    CheckConstraint,
    DateField,
    DateTimeField,
    DecimalField,
    F,
    ForeignKey,
    Index,
    IntegerField,
    PositiveSmallIntegerField,
    Q,
    TextChoices,
    TextField,
    UniqueConstraint,
)
from django.utils.timezone import now

from apps.models import BaseModel, TimeStampedModel


class Payment(TimeStampedModel):
    class Status(TextChoices):
        PENDING = "pending", "Kutilmoqda"
        PAID = "paid", "To'landi"
        OVERDUE = "overdue", "Muddati o'tdi"
        CANCELLED = "cancelled", "Bekor qilindi"
        REFUNDED = "refunded", "Qaytarildi"

    class Method(TextChoices):
        CASH = "cash", "Naqd"
        CARD = "card", "Karta"
        TRANSFER = "transfer", "Bank o'tkazmasi"
        ONLINE = "online", "Onlayn"

    student = ForeignKey("apps.Student", PROTECT, related_name="payments")
    group = ForeignKey("apps.Group", PROTECT, related_name="payments", null=True, blank=True)
    branch = ForeignKey("apps.Branch", PROTECT, related_name="payments", null=True, blank=True)

    amount = DecimalField(max_digits=12, decimal_places=2)
    discount = DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = DecimalField(max_digits=12, decimal_places=2)

    method = CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    status = CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    period_month = PositiveSmallIntegerField(help_text="1–12")
    period_year = PositiveSmallIntegerField()

    due_date = DateField()
    paid_at = DateTimeField(null=True, blank=True)

    receipt_number = CharField(max_length=100, unique=True, blank=True)
    comment = TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["status", "paid_at"]),
        ]
        constraints = [
            CheckConstraint(condition=Q(final_amount__gte=0), name="payment_final_amount_not_negative"),
            CheckConstraint(condition=Q(discount__gte=0), name="payment_discount_not_negative"),
        ]

    def __str__(self):
        return f"{self.student} | {self.final_amount} | {self.status}"

    def clean(self):
        super().clean()
        if self.amount is not None and self.discount is not None:
            if self.discount > self.amount:
                self.discount = self.amount

    def save(self, *args, **kwargs):
        self.final_amount = max(Decimal("0"), self.amount - self.discount)

        self.full_clean()

        if self.status == self.Status.PAID and not self.paid_at:
            from django.utils import timezone

            self.paid_at = timezone.now()
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# DEBT (mavjud model — o'zgartirilmadi)
# ─────────────────────────────────────────────

from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now


class Debt(BaseModel):
    class Status(TextChoices):
        UNPAID = "unpaid", "To'lanmagan"
        PARTIALLY_PAID = "partially_paid", "Qisman to'langan"
        PAID = "paid", "To'liq to'langan"

    student = ForeignKey("apps.Student", PROTECT, related_name="debts")
    group = ForeignKey("apps.Group", PROTECT, related_name="debts")
    amount = DecimalField(max_digits=12, decimal_places=2)
    due_date = DateField()
    status = CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.student} | {self.group} | {self.amount} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        while now().date() > self.due_date:
            self.amount += self.amount * Decimal("0.10")
            self.due_date += relativedelta(months=1)

        super().save(*args, **kwargs)

# ─────────────────────────────────────────────
# EXPENSE CATEGORY
# Kategoriyalar: ijara, maosh, marketing...
# Har bir markaz o'zining kategoriyalarini yaratadi
# ─────────────────────────────────────────────


class ExpenseCategory(BaseModel):
    """
    Xarajat kategoriyalari.

    Tizimda ikkita tur bo'ladi:
    - is_system=True  → EduMRX tomonidan default yaratilgan (o'chirib bo'lmaydi)
    - is_system=False → Director o'zi yaratgan
    """

    class Icon(TextChoices):
        BUILDING = "building", "Bino/Ijara"
        SALARY = "salary", "Maosh"
        MARKETING = "marketing", "Marketing"
        UTILITIES = "utilities", "Kommunal"
        EQUIPMENT = "equipment", "Jihozlar"
        INTERNET = "internet", "Internet"
        CLEANING = "cleaning", "Tozalik"
        TRANSPORT = "transport", "Transport"
        EDUCATION = "education", "Ta'lim materiallari"
        OTHER = "other", "Boshqa"

    center = ForeignKey(
        "apps.Center",
        PROTECT,
        related_name="expense_categories",
        null=True,
        blank=True,
        help_text="null bo'lsa — tizim kategoriyasi (barcha markazlar uchun)",
    )
    name = CharField(max_length=100)
    icon = CharField(max_length=20, choices=Icon.choices, default=Icon.OTHER)
    is_system = BooleanField(default=False, help_text="Tizim tomonidan yaratilgan kategoriya")
    is_active = BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            UniqueConstraint(fields=["center", "name"], name="unique_category_per_center"),
        ]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
# EXPENSE
# Oquv markazning xarajatlari
# ─────────────────────────────────────────────


class Expense(TimeStampedModel):
    class Status(TextChoices):
        PLANNED = "planned", "Rejalashtirilgan"
        DONE = "done", "Bajarildi"
        CANCELLED = "cancelled", "Bekor qilindi"

    class Method(TextChoices):
        CASH = "cash", "Naqd"
        CARD = "card", "Karta"
        TRANSFER = "transfer", "Bank o'tkazmasi"
        ONLINE = "online", "Onlayn"

    center = ForeignKey("apps.Center", PROTECT, related_name="expenses")
    branch = ForeignKey(
        "apps.Branch",
        PROTECT,
        related_name="expenses",
        null=True,
        blank=True,
        help_text="Aniq bir filialga tegishli bo'lsa; null = umumiy markaz xarajati",
    )
    category = ForeignKey(
        ExpenseCategory,
        SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )

    title = CharField(max_length=200, help_text="Xarajat nomi, masalan: 'May oyi ijarasi'")
    amount = DecimalField(max_digits=12, decimal_places=2)
    method = CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    status = CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)

    expense_date = DateField(help_text="Xarajat qilingan sana")
    paid_at = DateTimeField(null=True, blank=True)

    period_month = PositiveSmallIntegerField(null=True, blank=True, help_text="1–12, takroriy xarajatlar uchun")
    period_year = PositiveSmallIntegerField(null=True, blank=True)

    # Kim amalga oshirdi (admin yoki director)
    performed_by = ForeignKey(
        "apps.User",
        SET_NULL,
        null=True,
        blank=True,
        related_name="expenses_performed",
    )

    receipt_image = CharField(
        max_length=500,
        blank=True,
        help_text="Supabase Storage dagi chek/hujjat URL",
    )
    comment = TextField(blank=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]
        constraints = [
            CheckConstraint(condition=Q(amount__gt=0), name="expense_amount_positive"),
        ]

    def __str__(self):
        return f"{self.title} | {self.amount} | {self.expense_date}"

    def save(self, *args, **kwargs):
        if self.status == self.Status.PAID and not self.paid_at:
            from django.utils import timezone

            self.paid_at = timezone.now()
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# INCOME (qo'shimcha kirimlar)
# Student to'lovlaridan tashqari boshqa kirimlar:
# - Xona ijarasi (joy ijaraga berish)
# - Grant, subsidiya
# - Konsultatsiya
# - Boshqa kirimlar
# ─────────────────────────────────────────────


class IncomeCategory(BaseModel):
    center = ForeignKey(
        "apps.Center",
        PROTECT,
        related_name="income_categories",
        null=True,
        blank=True,
    )
    name = CharField(max_length=100)
    is_system = BooleanField(default=False)
    is_active = BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            UniqueConstraint(fields=["center", "name"], name="unique_income_category_per_center"),
        ]

    def __str__(self):
        return self.name


class Income(TimeStampedModel):
    class Method(TextChoices):
        CASH = "cash", "Naqd"
        CARD = "card", "Karta"
        TRANSFER = "transfer", "Bank o'tkazmasi"
        ONLINE = "online", "Onlayn"

    center = ForeignKey("apps.Center", PROTECT, related_name="incomes")
    branch = ForeignKey("apps.Branch", PROTECT, related_name="incomes", null=True, blank=True)
    category = ForeignKey(IncomeCategory, SET_NULL, null=True, blank=True, related_name="incomes")

    title = CharField(max_length=200)
    amount = DecimalField(max_digits=12, decimal_places=2)
    method = CharField(max_length=20, choices=Method.choices, default=Method.CASH)

    income_date = DateField()
    received_by = ForeignKey(
        "apps.User",
        SET_NULL,
        null=True,
        blank=True,
        related_name="incomes_received",
    )

    receipt_image = CharField(max_length=500, blank=True)
    comment = TextField(blank=True)

    class Meta:
        ordering = ["-income_date", "-created_at"]
        constraints = [
            CheckConstraint(condition=Q(amount__gt=0), name="income_amount_positive"),
        ]

    def __str__(self):
        return f"{self.title} | {self.amount} | {self.income_date}"


class Subscription(TimeStampedModel):
    class Plan(TextChoices):
        MONTHLY = "monthly", "Oylik"
        QUARTERLY = "quarterly", "Choraklik (3 oy)"
        YEARLY = "yearly", "Yillik"

    class Status(TextChoices):
        ACTIVE = "active", "Faol"
        EXPIRED = "expired", "Muddati tugagan"
        CANCELLED = "cancelled", "Bekor qilindi"
        TRIAL = "trial", "Sinov davri"
        PENDING = "pending", "To'lov kutilmoqda"

    center = ForeignKey("apps.Center", PROTECT, related_name="subscriptions")

    plan = CharField(max_length=20, choices=Plan.choices, default=Plan.MONTHLY)
    status = CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    amount = DecimalField(max_digits=12, decimal_places=2, help_text="Obuna narxi")
    discount = DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = DecimalField(max_digits=12, decimal_places=2)

    start_date = DateField()
    end_date = DateField()
    next_billing_date = DateField(null=True, blank=True)

    paid_at = DateTimeField(null=True, blank=True)

    # O'quvchilar soni limiti
    student_limit = IntegerField(default=100, help_text="Ruxsat etilgan max o'quvchi soni")
    branch_limit = IntegerField(default=1, help_text="Ruxsat etilgan max filial soni")

    transaction_id = CharField(max_length=200, blank=True, help_text="To'lov tizimidan kelgan ID")
    invoice_number = CharField(max_length=100, unique=True, blank=True)
    comment = TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            CheckConstraint(condition=Q(final_amount__gte=0), name="subscription_final_amount_not_negative"),
            CheckConstraint(condition=Q(end_date__gt=F("start_date")), name="subscription_end_after_start"),
        ]

    def __str__(self):
        return f"{self.center} | {self.plan} | {self.status} | {self.end_date}"

    def save(self, *args, **kwargs):
        self.final_amount = max(Decimal("0"), self.amount - self.discount)
        if self.status == self.Status.ACTIVE and not self.paid_at:
            from django.utils import timezone

            self.paid_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        from django.utils import timezone

        return self.status == self.Status.ACTIVE and self.end_date >= timezone.now().date()
