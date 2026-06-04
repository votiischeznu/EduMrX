from decimal import Decimal

from django.db.models import (
    DateField, CharField, TextChoices, DateTimeField, TextField,
    PositiveSmallIntegerField, ForeignKey, DecimalField, PROTECT, CheckConstraint, Q
)

from apps.models import BaseModel
from apps.models.users import TimeStampedModel


class Payment(TimeStampedModel):
    class Status(TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    class Method(TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        TRANSFER = "transfer", "Bank Transfer"
        ONLINE = "online", "Online"

    student = ForeignKey('apps.Student', on_delete=PROTECT, related_name="payments")
    group = ForeignKey('apps.Group', on_delete=PROTECT, related_name="payments", null=True, blank=True)

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

        constraints = [
            CheckConstraint(condition=Q(final_amount__gte=0), name="payment_final_amount_not_negative"),
            CheckConstraint(condition=Q(discount__gte=0), name="payment_discount_not_negative")
        ]

    def __str__(self):
        return f"{self.student} | {self.final_amount} | {self.status}"

    def clean(self):
        super().clean()
        if self.amount is not None and self.discount is not None:
            if self.discount > self.amount:
                self.discount = self.amount

    def save(self, *args, **kwargs):
        self.full_clean()
        self.final_amount = max(Decimal("0"), self.amount - self.discount)
        if self.status == self.Status.PAID and not self.paid_at:
            from django.utils import timezone
            self.paid_at = timezone.now()

        super().save(*args, **kwargs)


class Debt(BaseModel):
    class Status(TextChoices):
        UNPAID = "unpaid", "To'lanmagan"
        PARTIALLY_PAID = "partially_paid", "Qisman to'langan"
        PAID = "paid", "To'liq to'langan"

    student = ForeignKey('apps.Student', on_delete=PROTECT, related_name="debts")
    group = ForeignKey('apps.Group', on_delete=PROTECT, related_name="debts")
    amount = DecimalField(max_digits=12, decimal_places=2)
    due_date = DateField()

    status = CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.student} | {self.group} | {self.amount} ({self.get_status_display()})"
