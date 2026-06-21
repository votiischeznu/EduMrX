from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from apps.models import Center, Payment, Debt, Branch


class DirectorFinanceService:
    @staticmethod
    def get_summary_data(centers, branch=None):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = start_of_month - timedelta(seconds=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        paid_qs = Payment.objects.filter(status=Payment.Status.PAID, student__center__in=centers)
        debt_qs = Debt.objects.filter(
            status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID],
            student__center__in=centers,
        )

        if branch is not None:
            paid_qs = paid_qs.filter(student__branch=branch)
            debt_qs = debt_qs.filter(student__branch=branch)

        total_revenue = paid_qs.aggregate(t=Sum("final_amount"))["t"] or 0
        month_revenue = paid_qs.filter(paid_at__gte=start_of_month).aggregate(t=Sum("final_amount"))["t"] or 0

        last_month_revenue = (
            paid_qs.filter(paid_at__gte=last_month_start, paid_at__lte=last_month_end).aggregate(t=Sum("final_amount"))[
                "t"
            ]
            or 0
        )
        month_revenue_change = (
            round((month_revenue - last_month_revenue) / last_month_revenue * 100, 1) if last_month_revenue else 0.0
        )

        pending_debts = debt_qs.aggregate(t=Sum("amount"))["t"] or 0
        pending_debts_students_count = debt_qs.values("student").distinct().count()

        last_month_debt = (
            debt_qs.filter(
                due_date__gte=last_month_start.date(),
                due_date__lte=last_month_end.date(),
            ).aggregate(t=Sum("amount"))["t"]
            or 0
        )
        pending_debts_change = (
            round((pending_debts - last_month_debt) / last_month_debt * 100, 1) if last_month_debt else 0.0
        )

        return {
            "total_revenue": float(total_revenue),
            "month_revenue": float(month_revenue),
            "month_revenue_change": month_revenue_change,
            "active_centers": centers.filter(status=Center.Status.ACTIVE).count(),
            "total_centers": centers.count(),
            "pending_debts": float(pending_debts),
            "pending_debts_students_count": pending_debts_students_count,
            "pending_debts_change": pending_debts_change,
        }


class DirectorFinanceChartService:
    MONTHS_UZ = ["Yan", "Fev", "Mar", "Apr", "May", "Iyn", "Iyl", "Avg", "Sen", "Okt", "Noy", "Dek"]

    @staticmethod
    def get_top_branches_yearly_chart(centers, year: int, branch=None):
        base_qs = Payment.objects.filter(
            status=Payment.Status.PAID,
            paid_at__year=year,
            student__center__in=centers,
        ).exclude(student__branch__isnull=True)

        if branch is not None:
            base_qs = base_qs.filter(student__branch=branch)
            top_branches = [{"student__branch_id": branch.id, "student__branch__name": branch.name}]
        else:
            top_branches = list(
                base_qs.values("student__branch_id", "student__branch__name")
                .annotate(total=Sum("final_amount"))
                .order_by("-total")[:5]
            )

        chart = []
        for month in range(1, 13):
            row = {"name": DirectorFinanceChartService.MONTHS_UZ[month - 1]}
            for idx, branch_row in enumerate(top_branches, start=1):
                income = (
                    base_qs.filter(
                        paid_at__month=month,
                        student__branch_id=branch_row["student__branch_id"],
                    ).aggregate(t=Sum("final_amount"))["t"]
                    or 0
                )
                row[f"c{idx}"] = float(income) / 1_000_000
            chart.append(row)

        keys_definition = {f"c{idx}": b["student__branch__name"] for idx, b in enumerate(top_branches, start=1)}
        total_sum = base_qs.aggregate(t=Sum("final_amount"))["t"] or 0

        return {
            "total_sum_formatted": f"{round(float(total_sum) / 1_000_000)}M UZS",
            "chart": chart,
            "keys_definition": keys_definition,
        }


class DirectorFinanceTransactionsService:
    @staticmethod
    def get_transactions_list_with_student(centers, page, per_page, branch=None):
        qs = Payment.objects.filter(status=Payment.Status.PAID, student__center__in=centers).order_by("-paid_at")
        if branch is not None:
            qs = qs.filter(student__branch=branch)

        total = qs.count()
        offset = (page - 1) * per_page
        payments = qs[offset : offset + per_page]

        data = [
            {
                "id": str(p.id),
                "student_name": p.student.full_name if p.student else None,
                "center_name": p.student.center.name if p.student and p.student.center else None,
                "amount": float(p.final_amount or 0),
                "payment_method": p.method,
                "created_at": p.paid_at,
            }
            for p in payments
        ]
        return data, total


class DirectorFinanceBranchesService:
    @staticmethod
    def get_branches_finance_list(centers, status_filter, search, sort_by, sort_dir, page, per_page):
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Annotate nomini 'students_total' deb o'zgartirdik (modeldagi property bilan to'qnashmasligi uchun)
        qs = Branch.objects.filter(center__in=centers).annotate(
            students_total=Count("students", distinct=True),
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
            "students": "students_total",
        }.get(sort_by, "month_revenue")

        qs = qs.order_by(
            F(sort_field).desc(nulls_last=True) if sort_dir != "asc" else F(sort_field).asc(nulls_last=True)
        )

        total = qs.count()
        offset = (page - 1) * per_page
        branches = qs[offset : offset + per_page]

        data = [
            {
                "id": str(b.id),
                "name": b.name,
                "students_count": b.students_total or 0,
                "month_revenue": float(b.month_revenue or 0),
                "total_revenue": float(b.total_revenue or 0),
                "status": b.status,
            }
            for b in branches
        ]
        return data, total
