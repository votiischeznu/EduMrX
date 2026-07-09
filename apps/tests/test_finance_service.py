from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from model_bakery import baker

from apps.models import Center, Debt, Payment, Student
from apps.service import FinanceCentersService, FinanceChartService, FinanceService


def make_payment(**kwargs):
    kwargs.setdefault("receipt_number", f"REC-{__import__('uuid').uuid4()}")
    kwargs.setdefault("discount", Decimal("0"))
    return baker.make(Payment, **kwargs)


@pytest.mark.django_db(transaction=True)
class TestFinanceService:
    def setup_method(self):
        Payment.objects.all().delete()
        Debt.objects.all().delete()
        Student.objects.all().delete()
        Center.objects.all().delete()

    def test_get_summary_data(self):
        now = timezone.now()
        student = baker.make(Student, _fill_optional=False)

        make_payment(
            student=student,
            status=Payment.Status.PAID,
            amount=Decimal("1000"),
            paid_at=now,
        )
        last_month = now - timedelta(days=32)
        make_payment(
            student=student,
            status=Payment.Status.PAID,
            amount=Decimal("500"),
            paid_at=last_month,
        )
        baker.make(Debt, amount=200, status=Debt.Status.UNPAID, _fill_optional=False)

        summary = FinanceService.get_summary_data()

        assert summary["total_revenue"] == 1500
        assert summary["month_revenue"] == 1000
        assert summary["pending_debts"] == 200

    def test_get_chart_data_week(self):
        now = timezone.now()
        student = baker.make(Student, _fill_optional=False)
        make_payment(
            student=student,
            status=Payment.Status.PAID,
            amount=Decimal("300"),
            paid_at=now,
        )

        data = FinanceChartService.get_chart_data(period="week")

        assert data[-1]["income"] == 300
        assert sum(d["income"] for d in data[:-1]) == 0

    def test_get_centers_finance_list(self):
        center = baker.make(Center, name="Test Academy", _fill_optional=False)
        student = baker.make(Student, center=center, _fill_optional=False)
        make_payment(
            student=student,
            status=Payment.Status.PAID,
            amount=Decimal("200"),
            paid_at=timezone.now(),
        )

        data, total, total_sum = FinanceCentersService.get_centers_finance_list(
            status_filter="all",
            search="Test Academy",
            sort_by="month_revenue",
            sort_dir="desc",
            page=1,
            per_page=10,
        )

        assert total == 1
        target_center = next((c for c in data if c["id"] == str(center.id)), None)
        assert target_center is not None
        assert target_center["month_revenue"] == 200
        assert target_center["total_revenue"] == 200
