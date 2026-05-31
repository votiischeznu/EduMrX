from datetime import date
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.pagination import StudentPagination
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from apps.models import Student, Teacher, Attendance, Center, Group, Payment
from apps.permissions import IsSuperAdmin
from apps.serializers import (
    StudentListSerializer, StudentDetailSerializer, AttendanceSerializer, TeacherDetailSerializer,
    TeacherListSerializer)
from apps.serializers.management_serializers import StudentCreateUpdateSerializer, TeacherCreateUpdateSerializer, \
    CenterCreateUpdateSerializer, CenterListSerializer, CenterDetailSerializer, DirectorCreateUpdateSerializer, \
    DirectorListSerializer


@extend_schema(tags=['ManagementStudent'])
class ManagementStudentListView(ListAPIView):
    serializer_class = StudentListSerializer
    pagination_class = StudentPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone", "user__email"]
    ordering_fields = ["enrolled_at", "status", "user__first_name"]
    ordering = ["-enrolled_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Student.objects.select_related("user", "center", "parent__user").filter(center__status="active")

        if user.is_super_admin: return qs
        if user.is_director: return qs.filter(center__director=user)
        if user.is_admin: return qs.filter(center__staff_members__user=user)
        if user.is_teacher:
            return qs.filter(enrollments__group__teacher__user=user).distinct()

        return Student.objects.none()


@extend_schema(tags=['ManagementStudent'])
class ManagementStudentDetailView(RetrieveAPIView):
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Student.objects.select_related("user", "center", "parent__user")

        if user.is_super_admin: return qs
        if user.is_director: return qs.filter(center__director=user)
        if user.is_admin: return qs.filter(center__staff_members__user=user)
        if user.is_teacher:
            return qs.filter(enrollments__group__teacher__user=user).distinct()

        return Student.objects.none()


@extend_schema(tags=['ManagementTeacher'])
class ManagementTeacherListView(ListAPIView):
    serializer_class = TeacherListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["centers", "specialization"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Teacher.objects.select_related("user", "centers")

        if user.is_super_admin: return qs
        if user.is_director: return qs.filter(centers__director=user)
        if user.is_admin: return qs.filter(centers__staff_members__user=user)
        if user.is_student:
            return qs.filter(teaching_groups__enrollments__student__user=user).distinct()

        return Teacher.objects.none()


@extend_schema(tags=['ManagementTeacher'])
class ManagementTeacherDetailView(RetrieveAPIView):
    serializer_class = TeacherDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Teacher.objects.select_related("user", "centers")

        if user.is_super_admin: return qs
        if user.is_director: return qs.filter(centers__director=user)
        if user.is_admin: return qs.filter(centers__staff_members__user=user)
        if user.is_student:
            return qs.filter(teaching_groups__enrollments__student__user=user).distinct()

        return Teacher.objects.none()


@extend_schema(tags=['ManagementAttendance'])
class ManagementAttendanceViewSet(ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["lesson", "student", "status", "lesson__group"]
    ordering = ["-marked_at"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        user = self.request.user
        qs = Attendance.objects.select_related("lesson__group", "student__user")

        if user.is_super_admin: return qs
        if user.is_director: return qs.filter(lesson__group__center__director=user)
        if user.is_admin: return qs.filter(lesson__group__center__staff_members__user=user)
        if user.is_teacher:
            return qs.filter(lesson__group__teacher__user=user)
        if user.is_student:
            return qs.filter(student__user=user)

        return Attendance.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_teacher:
            lesson = serializer.validated_data["lesson"]
            if lesson.group.teacher.user != user:
                raise PermissionDenied("Siz faqat o'zingiz dars o'tadigan guruhlarga davomat qila olasiz!")
        serializer.save()


class SuperAdminStudentListCreateView(ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    pagination_class = StudentPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["enrolled_at", "status"]
    ordering = ["-enrolled_at"]
    queryset = Student.objects.select_related("user", "center").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StudentCreateUpdateSerializer
        return StudentListSerializer


class SuperAdminStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = Student.objects.select_related("user", "center").all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return StudentCreateUpdateSerializer
        return StudentDetailSerializer


class SuperAdminTeacherListCreateView(ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = Teacher.objects.select_related("user").all()
    pagination_class = StudentPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["centers", "specialization"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["created_at", "specialization"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TeacherCreateUpdateSerializer
        return TeacherListSerializer


class SuperAdminTeacherDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = Teacher.objects.select_related("user").all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return TeacherCreateUpdateSerializer
        return TeacherDetailSerializer


@extend_schema(tags=['SuperAdminCenter'])
class SuperAdminCenterListCreateView(ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsSuperAdmin]
    queryset = Center.objects.select_related("director").all()
    pagination_class = StudentPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["name", "phone", "email", "director__first_name", "director__last_name"]
    ordering_fields = ["name", "created_at", "status"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CenterCreateUpdateSerializer
        return CenterListSerializer


@extend_schema(tags=['SuperAdminCenter'])
class SuperAdminCenterDetailView(RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsSuperAdmin]
    queryset = Center.objects.select_related("director").all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CenterCreateUpdateSerializer
        return CenterDetailSerializer


@extend_schema(tags=['SuperAdminDashboard'])
class SuperAdminDashboardView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        today = date.today()
        current_month = today.month
        current_year = today.year
        last_month = today - relativedelta(months=1)

        # ── CENTERS ──────────────────────────────────────────
        centers_qs = Center.objects.all()
        total_centers = centers_qs.count()
        active_centers = centers_qs.filter(status="active").count()
        suspended_centers = centers_qs.filter(status="suspended").count()

        # Obuna muddati 7 kun ichida tugaydigan markazlar
        week_later = today + relativedelta(days=7)
        expiring_soon = centers_qs.filter(
            subscription_expires__range=[today, week_later]
        ).values("id", "name", "subscription_expires")

        # ── STUDENTS ─────────────────────────────────────────
        students_qs = Student.objects.all()
        total_students = students_qs.filter(status="active").count()

        # Shu oy yangi qo'shilgan studentlar
        new_students_this_month = students_qs.filter(
            enrolled_at__month=current_month,
            enrolled_at__year=current_year,
        ).count()

        # O'tgan oy bilan solishtirish
        new_students_last_month = students_qs.filter(
            enrolled_at__month=last_month.month,
            enrolled_at__year=last_month.year,
        ).count()

        # ── TEACHERS ─────────────────────────────────────────
        total_teachers = Teacher.objects.count()

        # ── GROUPS ───────────────────────────────────────────
        active_groups = Group.objects.filter(status="active").count()

        # ── PAYMENTS ─────────────────────────────────────────
        paid_qs = Payment.objects.filter(status="paid")

        monthly_income = paid_qs.filter(
            period_month=current_month,
            period_year=current_year,
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        last_month_income = paid_qs.filter(
            period_month=last_month.month,
            period_year=last_month.year,
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        # O'sish foizi
        income_growth = None
        if last_month_income:
            income_growth = round(
                ((monthly_income - last_month_income) / last_month_income) * 100, 1
            )

        # Umumiy qarzdorlik
        total_debt = Payment.objects.filter(
            status="overdue"
        ).aggregate(total=Sum("final_amount"))["total"] or 0

        # ── ATTENDANCE ───────────────────────────────────────
        attendance_qs = Attendance.objects.filter(
            lesson__date__month=current_month,
            lesson__date__year=current_year,
        )
        total_att = attendance_qs.count()
        present_att = attendance_qs.filter(status="present").count()
        attendance_rate = (
            round((present_att / total_att) * 100, 1) if total_att > 0 else 0
        )

        # ── TOP CENTERS (daromad bo'yicha) ───────────────────
        top_centers = (
            Center.objects.filter(
                groups__payments__status="paid",
                groups__payments__period_month=current_month,
                groups__payments__period_year=current_year,
            )
            .annotate(income=Sum("groups__payments__final_amount"))
            .order_by("-income")
            .values("id", "name", "income")[:5]
        )

        return Response({
            # Centers
            "centers": {
                "total": total_centers,
                "active": active_centers,
                "suspended": suspended_centers,
                "expiring_soon": list(expiring_soon),
            },

            # Students
            "students": {
                "total_active": total_students,
                "new_this_month": new_students_this_month,
                "new_last_month": new_students_last_month,
            },

            # Teachers & Groups
            "teachers": {"total": total_teachers},
            "groups": {"active": active_groups},

            # Finance
            "finance": {
                "monthly_income": monthly_income,
                "last_month_income": last_month_income,
                "income_growth_percent": income_growth,
                "total_overdue_debt": total_debt,
            },

            # Attendance
            "attendance": {
                "rate_percent": attendance_rate,
                "total_records": total_att,
                "present_count": present_att,
            },

            # Top centers
            "top_centers_by_income": list(top_centers),
        })


@extend_schema(tags=['AdminDashboard'])
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Faqat admin va director uchun
        if not (user.is_admin or user.is_director):
            return Response({"detail": "Ruxsat yo'q."}, status=403)

        today = date.today()
        current_month = today.month
        current_year = today.year
        last_month = today - relativedelta(months=1)

        # ── O'Z MARKAZI ──────────────────────────────────────
        if user.is_director:
            center = Center.objects.filter(director=user).first()
        else:
            center = getattr(user.staff_profile, "center", None)

        if not center:
            return Response({"detail": "Markaz topilmadi."}, status=404)

        # ── STUDENTS ─────────────────────────────────────────
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

        # Status bo'yicha breakdown
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

@extend_schema(tags=['SuperAdminDirector'])
class SuperAdminDirectorListCreateView(ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = User.objects.filter(role=User.Role.DIRECTOR)
    pagination_class = StudentPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering_fields = ["created_at", "first_name"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorCreateUpdateSerializer
        return DirectorListSerializer


@extend_schema(tags=['SuperAdminDirector'])
class SuperAdminDirectorDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = User.objects.filter(role=User.Role.DIRECTOR)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return DirectorCreateUpdateSerializer
        return DirectorListSerializer