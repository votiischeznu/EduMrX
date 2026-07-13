from datetime import timedelta

from django.db.models import Count, F, Q, Sum
from django.utils import timezone

from apps.models import Center, Debt, Payment
from apps.utils.constants import DAYS_UZ


def calculate_change(current, previous):
    if not previous or previous == 0:
        return 0.0
    return round(float((current - previous) / previous * 100), 1)


class FinanceService:
    @staticmethod
    def get_summary_data():
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = start_of_month - timedelta(seconds=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        paid_qs = Payment.objects.filter(status=Payment.Status.PAID)
        total_revenue = paid_qs.aggregate(t=Sum("final_amount"))["t"] or 0
        month_revenue = paid_qs.filter(paid_at__gte=start_of_month).aggregate(t=Sum("final_amount"))["t"] or 0

        last_month_revenue = (
            paid_qs.filter(paid_at__gte=last_month_start, paid_at__lte=last_month_end).aggregate(t=Sum("final_amount"))[
                "t"
            ]
            or 0
        )
        month_revenue_change = calculate_change(month_revenue, last_month_revenue)

        debt_qs = Debt.objects.filter(status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID])
        pending_debts = debt_qs.aggregate(t=Sum("amount"))["t"] or 0
        pending_debts_students_count = debt_qs.values("student").distinct().count()

        last_month_debt = (
            Debt.objects.filter(
                status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID],
                due_date__gte=last_month_start.date(),
                due_date__lte=last_month_end.date(),
            ).aggregate(t=Sum("amount"))["t"]
            or 0
        )

        pending_debts_change = (
            round((pending_debts - last_month_debt) / last_month_debt * 100, 1) if last_month_debt else 0.0
        )

        return {
            "total_revenue": total_revenue,
            "month_revenue": month_revenue,
            "month_revenue_change": month_revenue_change,
            "active_centers": Center.objects.filter(status=Center.Status.ACTIVE).count(),
            "total_centers": Center.objects.count(),
            "pending_debts": pending_debts,
            "pending_debts_students_count": pending_debts_students_count,
            "pending_debts_change": pending_debts_change,
        }


class FinanceChartService:
    @staticmethod
    def get_chart_data(period: str) -> list:
        now = timezone.now()
        data = []

        if period == "week":
            for i in range(6, -1, -1):
                day = now - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

                income = (
                    Payment.objects.filter(
                        status=Payment.Status.PAID,
                        paid_at__gte=day_start,
                        paid_at__lte=day_end,
                    ).aggregate(t=Sum("final_amount"))["t"]
                    or 0
                )

                data.append(
                    {
                        "label": DAYS_UZ[day.weekday()],
                        "income": income,
                        "expense": 0,
                    }
                )

        elif period == "month":
            for month in range(1, now.month + 1):
                income = (
                    Payment.objects.filter(
                        status=Payment.Status.PAID,
                        paid_at__year=now.year,
                        paid_at__month=month,
                    ).aggregate(t=Sum("final_amount"))["t"]
                    or 0
                )

                data.append(
                    {
                        "label": FinanceChartService.MONTHS_UZ[month - 1],
                        "income": income,
                        "expense": 0,
                    }
                )

        elif period == "year":
            for i in range(4, -1, -1):
                year = now.year - i
                income = (
                    Payment.objects.filter(
                        status=Payment.Status.PAID,
                        paid_at__year=year,
                    ).aggregate(t=Sum("final_amount"))["t"]
                    or 0
                )

                data.append(
                    {
                        "label": str(year),
                        "income": income,
                        "expense": 0,
                    }
                )

        return data

    @staticmethod
    def get_top_centers_yearly_chart(year: int) -> dict:
        """
        12 oylik, top-5 markaz bo'yicha daromad trendi.
        TZ bo'lim 3: /api/v1/super-admin/analytics/chart/?year=2026
        """
        top_center_ids = list(
            Payment.objects.filter(
                status=Payment.Status.PAID,
                paid_at__year=year,
            )
            .values("student__center_id", "student__center__name")
            .annotate(total=Sum("final_amount"))
            .order_by("-total")[:5]
        )

        chart = []
        for month in range(1, 13):
            row = {"name": FinanceChartService.MONTHS_UZ[month - 1]}
            for idx, center_row in enumerate(top_center_ids, start=1):
                center_id = center_row["student__center_id"]
                income = (
                    Payment.objects.filter(
                        status=Payment.Status.PAID,
                        paid_at__year=year,
                        paid_at__month=month,
                        student__center_id=center_id,
                    ).aggregate(t=Sum("final_amount"))["t"]
                    or 0
                )
                row[f"c{idx}"] = float(income) / 1_000_000  # millionlarda, TZ namunasiga mos
            chart.append(row)

        keys_definition = {
            f"c{idx}": center_row["student__center__name"] for idx, center_row in enumerate(top_center_ids, start=1)
        }

        total_sum = (
            Payment.objects.filter(status=Payment.Status.PAID, paid_at__year=year).aggregate(t=Sum("final_amount"))["t"]
            or 0
        )

        return {
            "total_sum_formatted": f"{round(float(total_sum) / 1_000_000)}M UZS",
            "chart": chart,
            "keys_definition": keys_definition,
        }


class FinanceCentersService:
    @staticmethod
    def get_centers_finance_list(status_filter, search, sort_by, sort_dir, page, per_page):
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        qs = Center.objects.select_related("director").annotate(
            students_count=Count("students", distinct=True),
            month_revenue=Sum(
                "students__payments__final_amount",
                filter=Q(
                    students__payments__status=Payment.Status.PAID,
                    students__payments__paid_at__gte=start_of_month,
                ),
            ),
            total_revenue=Sum(
                "students__payments__final_amount",
                filter=Q(students__payments__status=Payment.Status.PAID),
            ),
        )

        if status_filter != "all":
            qs = qs.filter(status=status_filter)

        if search:
            qs = qs.filter(name__icontains=search)

        sort_field = {
            "month_revenue": "month_revenue",
            "total_revenue": "total_revenue",
            "students": "students_count",
        }.get(sort_by, "month_revenue")

        if sort_dir == "asc":
            qs = qs.order_by(F(sort_field).asc(nulls_last=True))
        else:
            qs = qs.order_by(F(sort_field).desc(nulls_last=True))

        total = qs.count()
        total_revenue_sum = (
            Payment.objects.filter(status=Payment.Status.PAID).aggregate(t=Sum("final_amount"))["t"] or 0
        )

        offset = (page - 1) * per_page
        centers = qs[offset : offset + per_page]

        data = [
            {
                "id": str(c.id),
                "name": c.name,
                "director": c.director.full_name if c.director else None,
                "students_count": c.students_count or 0,
                "month_revenue": c.month_revenue or 0,
                "total_revenue": c.total_revenue or 0,
                "status": c.status,
            }
            for c in centers
        ]
        return data, total, total_revenue_sum


class FinanceTransactionsService:
    @staticmethod
    def get_transactions_list(page, per_page, include_student=False):
        qs = (
            Payment.objects.filter(status=Payment.Status.PAID)
            .select_related("student__user", "student__center")
            .order_by("-paid_at")
        )

        total = qs.count()
        offset = (page - 1) * per_page
        payments = qs[offset : offset + per_page]

        data = []
        for p in payments:
            item = {
                "id": str(p.id),
                "amount": p.final_amount,
                "payment_method": p.method,
                "created_at": p.paid_at,
                "center_name": p.student.center.name if p.student and p.student.center else None,
            }
            if include_student:
                item["student_name"] = p.student.full_name if p.student else None

            data.append(item)

        return data, total
