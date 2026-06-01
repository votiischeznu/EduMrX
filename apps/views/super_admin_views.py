from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Student, Teacher, Attendance, Center, Group, Payment, User
from apps.pagination import StudentPagination
from apps.permissions import IsSuperAdmin
from apps.serializers import (
    StudentListSerializer, StudentDetailSerializer, TeacherDetailSerializer,
    TeacherListSerializer, StudentCreateUpdateSerializer, TeacherCreateUpdateSerializer, CenterCreateUpdateSerializer,
    CenterListSerializer, CenterDetailSerializer, DirectorCreateUpdateSerializer, DirectorListSerializer)

@extend_schema(tags=['SuperAdminStudent'])
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


@extend_schema(tags=['SuperAdminStudent'])
class SuperAdminStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = Student.objects.select_related("user", "center").all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return StudentCreateUpdateSerializer
        return StudentDetailSerializer


@extend_schema(tags=['SuperAdminTeacher'])
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


@extend_schema(tags=['SuperAdminTeacher'])
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
