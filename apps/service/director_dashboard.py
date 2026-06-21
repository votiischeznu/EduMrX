from django.db.models import Sum, Count, Q, DecimalField
from django.db.models.functions import TruncMonth
from datetime import date

from rest_framework.exceptions import NotFound

from apps.models import Payment, Debt, Group, Student, Center


def get_director_centers(user):
    return Center.objects.filter(director=user)


def get_single_center_or_404(user):
    center = get_director_centers(user).first()
    if not center:
        raise NotFound("Sizga biriktirilgan markaz topilmadi.")
    return center



def get_dashboard_data(center):
    today = date.today()

    total_students = center.students.filter(user__is_deleted=False).count()
    active_students = center.students.filter(status=Student.Status.ACTIVE, user__is_deleted=False).count()
    total_teachers = center.teachers.filter(user__is_deleted=False).count()
    total_groups = center.groups.count()
    active_groups = center.groups.filter(status=Group.Status.ACTIVE).count()

    monthly_revenue = Payment.objects.filter(
        student__center=center, status=Payment.Status.PAID, paid_at__year=today.year, paid_at__month=today.month
    ).aggregate(total=Sum("final_amount", default=0))["total"]

    total_debt = Debt.objects.filter(
        student__center=center, status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID]
    ).aggregate(total=Sum("amount", default=0))["total"]

    # Chart ma'lumotlari
    revenue_chart = (
        Payment.objects.filter(student__center=center, status=Payment.Status.PAID)
        .annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(revenue=Sum("final_amount", output_field=DecimalField()))
        .order_by("month")
    )

    chart_data = [
        {"month": e["month"].strftime("%Y-%m"), "revenue": float(e["revenue"])} for e in revenue_chart if e["month"]
    ]

    # Guruhlar va to'lovlar
    top_groups = list(
        Group.objects.filter(center=center)
        .annotate(revenue=Sum("payments__final_amount", filter=Q(payments__status=Payment.Status.PAID), default=0))
        .order_by("-revenue")[:5]
        .values("id", "name", "student_count", "status", "revenue")
    )

    recent_payments = (
        Payment.objects.filter(student__center=center, status=Payment.Status.PAID)
        .select_related("student__user", "group")
        .order_by("-paid_at")[:10]
    )

    recent_payments_data = [
        {
            "student": p.student.full_name,
            "group": p.group.name if p.group else None,
            "amount": float(p.final_amount),
            "method": p.method,
            "paid_at": p.paid_at,
        }
        for p in recent_payments
    ]

    return {
        "kpi": {
            "total_students": total_students,
            "active_students": active_students,
            "total_teachers": total_teachers,
            "total_groups": total_groups,
            "active_groups": active_groups,
            "monthly_revenue": float(monthly_revenue),
            "total_debt": float(total_debt),
        },
        "revenue_chart": chart_data,
        "group_distribution": {
            g["status"]: g["count"] for g in center.groups.values("status").annotate(count=Count("id"))
        },
        "top_groups": top_groups,
        "recent_payments": recent_payments_data,
    }
