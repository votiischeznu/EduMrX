from datetime import timedelta

from django.db.models import Case, Count, DecimalField, F, Q, Sum, When
from django.db.models.functions import ExtractYear, TruncDay, TruncMonth
from django.db.models.query import QuerySet
from django.utils import timezone

from apps.models import Center, Debt, Payment
from apps.utils import DAY_NAMES, MONTH_NAMES


def calculate_change(current, previous):
    if not previous or previous == 0:
        return 0.0
    return round(float((current - previous) / previous * 100), 1)


class FinanceService:
    @staticmethod
    def get_payment_totals(qs: QuerySet) -> dict[str, float]:
        totals = qs.aggregate(
            total_amount=Sum("final_amount"),
            paid_total=Sum(
                Case(
                    When(status=Payment.Status.PAID, then=F("final_amount")),
                    default=0,
                    output_field=DecimalField(),
                )
            ),
            pending_total=Sum(
                Case(
                    When(status=Payment.Status.PENDING, then=F("final_amount")),
                    default=0,
                    output_field=DecimalField(),
                )
            ),
            overdue_total=Sum(
                Case(
                    When(status=Payment.Status.OVERDUE, then=F("final_amount")),
                    default=0,
                    output_field=DecimalField(),
                )
            ),
        )
        return {
            "total_amount": float(totals["total_amount"] or 0),
            "paid_total": float(totals["paid_total"] or 0),
            "pending_total": float(totals["pending_total"] or 0),
            "overdue_total": float(totals["overdue_total"] or 0),
        }

    @staticmethod
    def get_summary_data() -> dict:
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
            start_date = now - timedelta(days=6)
            daily_income = (
                Payment.objects.filter(
                    status=Payment.Status.PAID,
                    paid_at__gte=start_date.replace(hour=0, minute=0, second=0, microsecond=0),
                )
                .annotate(day=TruncDay("paid_at"))
                .values("day")
                .annotate(total=Sum("final_amount"))
            )
            daily_map = {item["day"].date(): item["total"] or 0 for item in daily_income}
            for i in range(6, -1, -1):
                day = (now - timedelta(days=i)).date()
                data.append(
                    {
                        "label": DAY_NAMES[day.weekday()],
                        "income": daily_map.get(day, 0),
                        "expense": 0,
                    }
                )

        elif period == "month":
            monthly_income = (
                Payment.objects.filter(
                    status=Payment.Status.PAID,
                    paid_at__year=now.year,
                )
                .annotate(month=TruncMonth("paid_at"))
                .values("month")
                .annotate(total=Sum("final_amount"))
            )
            monthly_map = {item["month"].month: item["total"] or 0 for item in monthly_income}
            for month in range(1, now.month + 1):
                data.append(
                    {
                        "label": MONTH_NAMES[month - 1],
                        "income": monthly_map.get(month, 0),
                        "expense": 0,
                    }
                )

        elif period == "year":
            yearly_income = (
                Payment.objects.filter(
                    status=Payment.Status.PAID,
                    paid_at__year__gte=now.year - 4,
                    paid_at__year__lte=now.year,
                )
                .annotate(year=ExtractYear("paid_at"))
                .values("year")
                .annotate(total=Sum("final_amount"))
            )
            yearly_map = {item["year"]: item["total"] or 0 for item in yearly_income}
            for i in range(4, -1, -1):
                year = now.year - i
                data.append(
                    {
                        "label": str(year),
                        "income": yearly_map.get(year, 0),
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

        # Optimization: Fetch all monthly data in one query
        center_ids = [c["student__center_id"] for c in top_center_ids]
        monthly_data = (
            Payment.objects.filter(
                status=Payment.Status.PAID,
                paid_at__year=year,
                student__center_id__in=center_ids,
            )
            .annotate(month=TruncMonth("paid_at"))
            .values("month", "student__center_id")
            .annotate(income=Sum("final_amount"))
        )

        # Pre-format data for easy access: {month: {center_id: income}}
        chart_data = {month: {cid: 0.0 for cid in center_ids} for month in range(1, 13)}
        for item in monthly_data:
            month = item["month"].month
            cid = item["student__center_id"]
            income = item["income"] or 0
            chart_data[month][cid] = float(income) / 1_000_000

        chart = []
        for month in range(1, 13):
            row = {"name": MONTH_NAMES[month - 1]}
            for idx, center_row in enumerate(top_center_ids, start=1):
                cid = center_row["student__center_id"]
                row[f"c{idx}"] = chart_data[month][cid]
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
    def get_centers_finance_list(
        status_filter: str, search: str | None, sort_by: str, sort_dir: str, page: int, per_page: int
    ) -> tuple[list[dict], int, float]:
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
        return data, total, float(total_revenue_sum)


class FinanceTransactionsService:
    @staticmethod
    def get_transactions_list(page: int, per_page: int, include_student: bool = False) -> tuple[list[dict], int]:
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
