from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Lesson, GroupStudent
from apps.models import Student, Teacher, Attendance, Center, Group, Payment


@extend_schema(tags=['AdminDashboard'])
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
        total_students = students_qs.filter(status="active").count()

        new_this_month = students_qs.filter(
            enrolled_at__month=current_month,
            enrolled_at__year=current_year,
        ).count()

        new_last_month = students_qs.filter(
            enrolled_at__month=last_month.month,
            enrolled_at__year=last_month.year,
        ).count()

        students_by_status = students_qs.values("status").annotate(count=Count("id"))

        # ── TEACHERS ─────────────────────────────────────────
        total_teachers = Teacher.objects.filter(centers=center).count()

        # ── GROUPS ───────────────────────────────────────────
        groups_qs = Group.objects.filter(center=center)
        active_groups = groups_qs.filter(status="active").count()
        completed_groups = groups_qs.filter(status="completed").count()

        # ── FINANCE ──────────────────────────────────────────
        payments_qs = Payment.objects.filter(group__center=center)

        monthly_income = payments_qs.filter(
            status="paid",
            period_month=current_month,
            period_year=current_year,
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        last_month_income = payments_qs.filter(
            status="paid",
            period_month=last_month.month,
            period_year=last_month.year,
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        income_growth = None
        if last_month_income:
            income_growth = round(
                ((monthly_income - last_month_income) / last_month_income) * 100, 1
            )

        # Qarzdor studentlar
        overdue_payments = payments_qs.filter(status="overdue")
        total_debt = overdue_payments.aggregate(
            total=Sum("final_amount")
        )["total"] or 0
        debtors_count = overdue_payments.values("student").distinct().count()

        # Kutilayotgan to'lovlar
        pending_income = payments_qs.filter(
            status="pending",
            period_month=current_month,
            period_year=current_year,
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        # ── ATTENDANCE ───────────────────────────────────────
        attendance_qs = Attendance.objects.filter(
            lesson__group__center=center,
            lesson__date__month=current_month,
            lesson__date__year=current_year,
        )
        total_att = attendance_qs.count()
        present_att = attendance_qs.filter(status="present").count()
        attendance_rate = (
            round((present_att / total_att) * 100, 1) if total_att > 0 else 0
        )

        # ── TOP GROUPS (davomat bo'yicha) ─────────────────────
        top_groups = (
            Group.objects.filter(center=center, status="active")
            .annotate(
                present_count=Count(
                    "lessons__attendances",
                    filter=Q(
                        lessons__attendances__status="present",
                        lessons__date__month=current_month,
                        lessons__date__year=current_year,
                    )
                )
            )
            .order_by("-present_count")
            .values("id", "name", "present_count")[:5]
        )

        return Response({
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
        })


User = get_user_model()


@extend_schema(tags=['StudentDashboard'])
class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.is_student:
            return Response({"detail": "Ruxsat yo'q."}, status=403)

        today = date.today()
        current_month = today.month
        current_year = today.year

        try:
            student = user.student_profile
        except Exception:
            return Response({"detail": "Student profil topilmadi."}, status=404)

        enrollments = GroupStudent.objects.filter(
            student=student, is_active=True
        ).select_related("group__teacher__user", "group__course")

        groups = []
        for enrollment in enrollments:
            group = enrollment.group
            groups.append({
                "id": group.id,
                "name": group.name,
                "course": group.course.name,
                "teacher": group.teacher.user.full_name,
                "lesson_days": group.lesson_days,
                "lesson_start_time": group.lesson_start_time,
                "lesson_end_time": group.lesson_end_time,
                "status": group.status,
            })

        # ── ATTENDANCE ───────────────────────────────────────
        attendance_qs = Attendance.objects.filter(student=student)

        total_att = attendance_qs.count()
        present_att = attendance_qs.filter(status="present").count()
        absent_att = attendance_qs.filter(status="absent").count()
        attendance_rate = (
            round((present_att / total_att) * 100, 1) if total_att > 0 else 0
        )

        # Shu oylik davomat
        monthly_att = attendance_qs.filter(
            lesson__date__month=current_month,
            lesson__date__year=current_year,
        )
        monthly_present = monthly_att.filter(status="present").count()
        monthly_total = monthly_att.count()
        monthly_rate = (
            round((monthly_present / monthly_total) * 100, 1) if monthly_total > 0 else 0
        )

        # ── PAYMENTS ─────────────────────────────────────────
        payments_qs = Payment.objects.filter(student=student)

        monthly_payment = payments_qs.filter(
            status="paid",
            period_month=current_month,
            period_year=current_year,
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        total_debt = payments_qs.filter(
            status="overdue"
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        pending_payment = payments_qs.filter(
            status="pending",
            period_month=current_month,
            period_year=current_year,
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        # Oxirgi 5 ta to'lov
        recent_payments = payments_qs.order_by("-created_at").values(
            "id", "final_amount", "status", "method",
            "period_month", "period_year", "paid_at"
        )[:5]

        # ── UPCOMING LESSONS ─────────────────────────────────
        upcoming_lessons = Lesson.objects.filter(
            group__enrollments__student=student,
            group__enrollments__is_active=True,
            date__gte=today,
        ).select_related("group__teacher__user").order_by("date")[:5].values(
            "id", "date", "group__name",
            "group__lesson_start_time", "group__lesson_end_time",
            "group__teacher__user__first_name",
            "group__teacher__user__last_name",
        )

        return Response({
            # Profil
            "profile": {
                "full_name": user.full_name,
                "phone": user.phone,
                "email": user.email,
                "avatar": request.build_absolute_uri(user.avatar.url) if user.avatar else None,
                "center": student.center.name,
                "status": student.status,
                "enrolled_at": student.enrolled_at,
            },

            # Guruhlar
            "groups": {
                "total": len(groups),
                "list": groups,
            },

            # Davomat
            "attendance": {
                "overall_rate": attendance_rate,
                "monthly_rate": monthly_rate,
                "total_present": present_att,
                "total_absent": absent_att,
                "monthly_present": monthly_present,
                "monthly_total": monthly_total,
            },

            # To'lovlar
            "payments": {
                "monthly_paid": monthly_payment,
                "total_debt": total_debt,
                "pending": pending_payment,
                "recent": list(recent_payments),
            },

            # Kelgusi darslar
            "upcoming_lessons": list(upcoming_lessons),
        })


@extend_schema(tags=['StudentStats'])
class StudentStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        active = Student.objects.filter(status=Student.Status.ACTIVE).count()
        new_this_month = Student.objects.filter(created_at__gte=start_of_month).count()
        minus_this_month = Student.objects.filter(
            status__in=[
                Student.Status.INACTIVE,
                Student.Status.GRADUATED,
                Student.Status.SUSPENDED,
            ],
            updated_at__gte=start_of_month,
        ).count()
        return Response({
            "active": active,
            "new_this_month": new_this_month,
            "minus_this_month": minus_this_month,
        })
