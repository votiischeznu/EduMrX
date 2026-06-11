from datetime import date

from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models.centers import Center
from apps.models.profiles import Student
from apps.models.payments import Payment, Debt
from apps.models.groups import Group
from apps.permissions import IsDirector
from apps.serializers.director import (
    DirectorStudentCreateSerializer,
    DirectorStudentDetailSerializer,
    DirectorStudentListSerializer,
)


def get_director_centers(user):
    return Center.objects.filter(director=user, status="active")


# ─── Dashboard ────────────────────────────────────────────────────────────────


class DirectorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    @extend_schema(tags=["1. Director"])
    def get(self, request):
        user = request.user
        center = Center.objects.filter(director=user).first()
        if not center:
            return Response(
                {"detail": "Sizga biriktirilgan markaz topilmadi."}, status=404
            )

        today = date.today()
        current_year = today.year
        current_month = today.month

        # ── KPI ──────────────────────────────────────────────────────────────
        total_students = center.students.filter(user__is_deleted=False).count()
        active_students = center.students.filter(
            status="active", user__is_deleted=False
        ).count()
        total_teachers = center.teachers.filter(user__is_deleted=False).count()
        total_groups = center.groups.count()
        active_groups = center.groups.filter(status="active").count()

        monthly_revenue = Payment.objects.filter(
            student__center=center,
            status="paid",
            period_year=current_year,
            period_month=current_month,
        ).aggregate(total=Sum("final_amount", default=0))["total"]

        total_debt = Debt.objects.filter(
            student__center=center,
            status__in=["unpaid", "partially_paid"],
        ).aggregate(total=Sum("amount", default=0))["total"]

        # ── Revenue chart (12 oy) ─────────────────────────────────────────────
        revenue_chart = (
            Payment.objects.filter(student__center=center, status="paid")
            .annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(revenue=Sum("final_amount", output_field=DecimalField()))
            .order_by("month")
        )
        chart_data = [
            {
                "month": entry["month"].strftime("%Y-%m"),
                "revenue": float(entry["revenue"]),
            }
            for entry in revenue_chart
            if entry["month"]
        ]

        # ── Group distribution ────────────────────────────────────────────────
        group_stats = center.groups.values("status").annotate(count=Count("id"))
        group_distribution = {g["status"]: g["count"] for g in group_stats}

        # ── Top 5 groups ──────────────────────────────────────────────────────
        top_groups = (
            Group.objects.filter(center=center)
            .annotate(
                revenue=Sum(
                    "payments__final_amount",
                    filter=Q(payments__status="paid"),
                    default=0,
                )
            )
            .order_by("-revenue")[:5]
            .values("id", "name", "student_count", "status", "revenue")
        )

        # ── Recent 10 payments ────────────────────────────────────────────────
        recent_payments = (
            Payment.objects.filter(student__center=center, status="paid")
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

        return Response(
            {
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
                "group_distribution": group_distribution,
                "top_groups": list(top_groups),
                "recent_payments": recent_payments_data,
            }
        )


# ─── Students ─────────────────────────────────────────────────────────────────


class DirectorStudentListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["enrolled_at", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Student.objects.filter(
            center__in=centers, user__is_deleted=False
        ).select_related("user", "center", "parent__user")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorStudentCreateSerializer
        return DirectorStudentListSerializer

    @extend_schema(tags=["2. Director — Students"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["2. Director — Students"])
    def post(self, request, *args, **kwargs):
        centers = get_director_centers(request.user)
        serializer = DirectorStudentCreateSerializer(
            data=request.data,
            context={"request": request, "centers": centers},
        )
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(
            DirectorStudentDetailSerializer(student).data,
            status=status.HTTP_201_CREATED,
        )


class DirectorStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Student.objects.filter(
            center__in=centers, user__is_deleted=False
        ).select_related("user", "center", "parent__user")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DirectorStudentCreateSerializer
        return DirectorStudentDetailSerializer

    @extend_schema(tags=["2. Director — Students"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["2. Director — Students"])
    def patch(self, request, *args, **kwargs):
        centers = get_director_centers(request.user)
        instance = self.get_object()
        serializer = DirectorStudentCreateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request, "centers": centers},
        )
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(DirectorStudentDetailSerializer(student).data)

    @extend_schema(tags=["2. Director — Students"])
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
