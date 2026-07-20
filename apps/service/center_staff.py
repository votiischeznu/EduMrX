from datetime import date
from typing import Any

from django.db.models import Sum, Q, QuerySet
from rest_framework.exceptions import NotFound

from apps.models import Center, Student, Teacher, Group, Course, Payment, Debt, User


def get_admin_centers(user: User) -> QuerySet[Center]:
    return Center.objects.filter(
        staff__user=user,
        staff__is_active=True,
    ).distinct()


def get_single_admin_center_or_404(user: User) -> Center:
    center = get_admin_centers(user).first()
    if not center:
        raise NotFound("Sizga biriktirilgan filial topilmadi.")
    return center


def get_center_analytics(center: Center) -> dict[str, Any]:
    students_qs = Student.objects.filter(center=center, user__is_deleted=False)
    teachers_qs = Teacher.objects.filter(centers=center, user__is_deleted=False)
    groups_qs = Group.objects.filter(center=center)
    courses_qs = Course.objects.filter(center=center)
    payments_qs = Payment.objects.filter(student__center=center)
    debts_qs = Debt.objects.filter(student__center=center)

    payments_summary = payments_qs.aggregate(
        total_paid=Sum("final_amount", filter=Q(status=Payment.Status.PAID)),
        total_pending=Sum("final_amount", filter=Q(status=Payment.Status.PENDING)),
        total_overdue=Sum("final_amount", filter=Q(status=Payment.Status.OVERDUE)),
    )
    debts_summary = debts_qs.aggregate(
        total_unpaid=Sum("amount", filter=~Q(status=Debt.Status.PAID)),
    )

    return {
        "center_id": center.id,
        "center_name": center.name,
        "students": {
            "total": students_qs.count(),
            "active": students_qs.filter(status=Student.Status.ACTIVE).count(),
        },
        "teachers": {
            "total": teachers_qs.count(),
        },
        "groups": {
            "total": groups_qs.count(),
            "active": groups_qs.filter(status=Group.Status.ACTIVE).count(),
        },
        "courses": {
            "total": courses_qs.count(),
        },
        "payments": {
            "total_paid": payments_summary["total_paid"] or 0,
            "total_pending": payments_summary["total_pending"] or 0,
            "total_overdue": payments_summary["total_overdue"] or 0,
        },
        "debts": {
            "total_unpaid": debts_summary["total_unpaid"] or 0,
        },
    }


def get_multi_center_analytics(centers: QuerySet[Center] | list[Center]) -> list[dict[str, Any]]:
    return [get_center_analytics(center) for center in centers]


def get_admin_dashboard_data(center: Center) -> dict[str, Any]:
    today = date.today()

    students_qs = Student.objects.filter(center=center, user__is_deleted=False)
    groups_qs = Group.objects.filter(center=center)

    payments_today_qs = Payment.objects.filter(
        student__center=center,
        paid_at__date=today,
        status=Payment.Status.PAID,
    )
    overdue_debts_qs = Debt.objects.filter(
        student__center=center,
        due_date__lt=today,
    ).exclude(status=Debt.Status.PAID)

    return {
        "students_total": students_qs.count(),
        "active_students": students_qs.filter(status=Student.Status.ACTIVE).count(),
        "groups_total": groups_qs.count(),
        "active_groups": groups_qs.filter(status=Group.Status.ACTIVE).count(),
        "payments_today_count": payments_today_qs.count(),
        "payments_today_sum": payments_today_qs.aggregate(s=Sum("final_amount"))["s"] or 0,
        "overdue_debts_count": overdue_debts_qs.count(),
        "overdue_debts_sum": overdue_debts_qs.aggregate(s=Sum("amount"))["s"] or 0,
    }
