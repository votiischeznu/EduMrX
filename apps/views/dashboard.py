from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import (
    Attendance,
    Center,
    Group,
    Payment,
    Student,
    Teacher,
)

User = get_user_model()


@extend_schema(tags=["AdminDashboard"])
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not (user.is_admin or user.is_director):
            return Response({"detail": "Ruxsat yo'q."}, status=403)

        today = date.today()
        current_month = today.month
        current_year = today.year
        last_month = today - relativedelta(months=1)

        if user.is_director:
            center = Center.objects.filter(director=user).first()
        else:
            center = getattr(user.staff_profile, "center", None)

        if not center:
            return Response({"detail": "Markaz topilmadi."}, status=404)

        students_qs = Student.objects.filter(center=center)
        total_students = students_qs.filter(status=Student.Status.ACTIVE).count()

        new_this_month = students_qs.filter(
            enrolled_at__month=current_month,
            enrolled_at__year=current_year,
        ).count()

        new_last_month = students_qs.filter(
            enrolled_at__month=last_month.month,
            enrolled_at__year=last_month.year,
        ).count()

        students_by_status = students_qs.values("status").annotate(count=Count("id"))

        # ===================== TEACHERS =====================
        total_teachers = Teacher.objects.filter(centers=center).count()

        # ===================== GROUPS ========================
        groups_qs = Group.objects.filter(center=center)
        active_groups = groups_qs.filter(status=Group.Status.ACTIVE).count()
        completed_groups = groups_qs.filter(status=Group.Status.COMPLETED).count()

        # ===================== FINANCE =======================
        payments_qs = Payment.objects.filter(group__center=center)

        monthly_income = (
            payments_qs.filter(
                status=Payment.Status.PAID,
                period_month=current_month,
                period_year=current_year,
            ).aggregate(total=Sum("final_amount"))["total"]
            or 0
        )

        last_month_income = (
            payments_qs.filter(
                status=Payment.Status.PAID,
                period_month=last_month.month,
                period_year=last_month.year,
            ).aggregate(total=Sum("final_amount"))["total"]
            or 0
        )

        income_growth = None
        if last_month_income:
            income_growth = round(((monthly_income - last_month_income) / last_month_income) * 100, 1)

        # Qarzdor studentlar
        overdue_payments = payments_qs.filter(status=Payment.Status.OVERDUE)
        total_debt = overdue_payments.aggregate(total=Sum("final_amount"))["total"] or 0
        debtors_count = overdue_payments.values("student").distinct().count()

        # Kutilayotgan to'lovlar
        pending_income = (
            payments_qs.filter(
                status=Payment.Status.PENDING,
                period_month=current_month,
                period_year=current_year,
            ).aggregate(total=Sum("final_amount"))["total"]
            or 0
        )

        # ===================== ATTENDANCE ====================
        attendance_qs = Attendance.objects.filter(
            lesson__group__center=center,
            lesson__date__month=current_month,
            lesson__date__year=current_year,
        )
        total_att = attendance_qs.count()
        present_att = attendance_qs.filter(status=Attendance.Status.PRESENT).count()
        attendance_rate = round((present_att / total_att) * 100, 1) if total_att > 0 else 0

        # ===================== TOP GROUPS (davomat bo'yicha) =
        top_groups = (
            Group.objects.filter(center=center, status=Group.Status.ACTIVE)
            .annotate(
                present_count=Count(
                    "lessons__attendances",
                    filter=Q(
                        lessons__attendances__status=Attendance.Status.PRESENT,
                        lessons__date__month=current_month,
                        lessons__date__year=current_year,
                    ),
                )
            )
            .order_by("-present_count")
            .values("id", "name", "present_count")[:5]
        )

        return Response(
            {
                # Markaz info
                "center": {
                    "id": center.id,
                    "name": center.name,
                    "address": center.address,
                    "latitude": center.latitude,
                    "longitude": center.longitude,
                    "status": center.status,
                    "subscription_expires": center.subscription_expires,
                    "is_subscription_active": center.is_subscription_active,
                },
                # Students
                "students": {
                    "total_active": total_students,
                    "new_this_month": new_this_month,
                    "new_last_month": new_last_month,
                    "by_status": list(students_by_status),
                },
                # Teachers & Groups
                "teachers": {"total": total_teachers},
                "groups": {
                    "active": active_groups,
                    "completed": completed_groups,
                },
                # Finance
                "finance": {
                    "monthly_income": monthly_income,
                    "last_month_income": last_month_income,
                    "income_growth_percent": income_growth,
                    "pending_income": pending_income,
                    "total_debt": total_debt,
                    "debtors_count": debtors_count,
                },
                # Attendance
                "attendance": {
                    "rate_percent": attendance_rate,
                    "total_records": total_att,
                    "present_count": present_att,
                },
                # Top groups
                "top_groups_by_attendance": list(top_groups),
            }
        )
