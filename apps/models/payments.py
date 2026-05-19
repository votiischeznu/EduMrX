import uuid
from decimal import Decimal

from django.db.models import DateField, CharField, UUIDField, TextChoices, DateTimeField, \
    Model, TextField, PositiveSmallIntegerField, ForeignKey, DecimalField, PROTECT


class Payment(Model):
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

    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} | {self.final_amount} | {self.status}"

    def save(self, *args, **kwargs):
        self.final_amount = max(Decimal("0"), self.amount - self.discount)
        super().save(*args, **kwargs)

class Debt(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = ForeignKey('apps.Student', on_delete=PROTECT, related_name="debts")
    group = ForeignKey('apps.Group', on_delete=PROTECT, related_name="debts")
    amount = DecimalField(max_digits=12, decimal_places=2, default=0)

    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "group")

    def __str__(self):
        return f"{self.student} owes {self.amount}"
