from datetime import date

from django.db.models import Count, Sum, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Student, Center, User, Payment
from apps.pagination import CustomPagination
from apps.permissions import IsSuperAdmin
from apps.serializers import (
    DirectorCreateUpdateSerializer,
    DirectorListSerializer,
    CenterListSerializer,
    CenterStudentCountSerializer,
    CenterDetailSerializer,
    StudentCreateUpdateSerializer,
    StudentDetailSerializer,
    StudentListSerializer,
)
from django.db.models.functions import TruncMonth
from apps.serializers.stats import SuperAdminDashboardSerializer

UZ_MONTHS = {
    1: "Yan",
    2: "Fev",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Iyun",
    7: "Iyul",
    8: "Avg",
    9: "Sen",
    10: "Okt",
    11: "Noy",
    12: "Dek",
}


def _get_12m_start(today: date) -> date:
    month = today.month
    year = today.year
    start_month = month + 1 if month < 12 else 1
    start_year = year if month < 12 else year + 1
    start_year -= 1
    return date(start_year, start_month, 1)


def _generate_empty_12m_dict(start_date: date) -> dict:
    """
    Oxirgi 12 oy uchun standart 0 qiymatli dict generatsiya qiladi.
    Bu bazada ma'lumot bo'lmagan bo'sh oylarni to'ldirish uchun kerak.
    """
    months_dict = {}
    current_date = start_date
    for _ in range(12):
        key = f"{current_date.year}-{current_date.month:02d}"
        months_dict[key] = {"month": UZ_MONTHS[current_date.month], "raw_amount": 0, "raw_count": 0}
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
    return months_dict


@extend_schema(tags=["Super Admin"], responses={200: SuperAdminDashboardSerializer})
class SuperAdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        first_of_month = today.replace(day=1)

        last_month_last_day = first_of_month - timezone.timedelta(days=1)
        last_month_first_day = last_month_last_day.replace(day=1)

        centers_agg = Center.objects.aggregate(
            total=Count("id"), active=Count("id", filter=Q(status=Center.Status.ACTIVE))
        )

        students_agg = Student.objects.aggregate(
            total=Count("id"), new_this_month=Count("id", filter=Q(created_at__date__gte=first_of_month))
        )

        revenue_this = (
            Payment.objects.filter(
                status=Payment.Status.PAID,
                created_at__date__gte=first_of_month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        revenue_last = (
            Payment.objects.filter(
                status=Payment.Status.PAID,
                created_at__date__gte=last_month_first_day,
                created_at__date__lte=last_month_last_day,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        if revenue_last > 0:
            pct_change = round(((revenue_this - revenue_last) / revenue_last) * 100, 1)
        else:
            pct_change = 100.0 if revenue_this > 0 else 0.0

        subs_agg = Center.objects.aggregate(
            trial=Count("id", filter=Q(plan=Center.Plan.TRIAL)),
            pro=Count("id", filter=Q(plan=Center.Plan.PRO)),
            enterprise=Count("id", filter=Q(plan=Center.Plan.ENTERPRISE)),
        )

        try:
            from apps.models import Notification

            open_tickets = Notification.objects.filter(notification_type="ticket", is_read=False).count()
        except Exception:
            open_tickets = 0

        start_12m = _get_12m_start(today)
        chart_master_dict = _generate_empty_12m_dict(start_12m)

        revenue_12m_qs = (
            Payment.objects.filter(status=Payment.Status.PAID, created_at__date__gte=start_12m)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(amount=Sum("amount"))
            .order_by("month")
        )
        for r in revenue_12m_qs:
            dt = r["month"]
            key = f"{dt.year}-{dt.month:02d}"
            if key in chart_master_dict:
                chart_master_dict[key]["raw_amount"] = int(r["amount"] or 0)

        student_growth_qs = (
            Student.objects.filter(created_at__date__gte=start_12m)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        for s in student_growth_qs:
            dt = s["month"]
            key = f"{dt.year}-{dt.month:02d}"
            if key in chart_master_dict:
                chart_master_dict[key]["raw_count"] = s["count"] or 0

        base_student_count = Student.objects.filter(created_at__date__lt=start_12m).count()

        revenue_12m = []
        student_growth = []
        cumulative = base_student_count

        for key in sorted(chart_master_dict.keys()):
            item = chart_master_dict[key]

            revenue_12m.append({"month": item["month"], "amount": item["raw_amount"]})

            cumulative += item["raw_count"]
            student_growth.append({"month": item["month"], "count": cumulative})

        total_centers = centers_agg["total"] or 1
        center_distribution = [
            {
                "name": "Trial",
                "value": round((subs_agg["trial"] or 0) / total_centers * 100),
                "color": "#A855F7",
            },
            {
                "name": "Pro",
                "value": round((subs_agg["pro"] or 0) / total_centers * 100),
                "color": "#10B981",
            },
            {
                "name": "Enterprise",
                "value": round((subs_agg["enterprise"] or 0) / total_centers * 100),
                "color": "#4F46E5",
            },
        ]

        top_qs = (
            Center.objects.filter(status=Center.Status.ACTIVE)
            .order_by("-total_students")
            .values("id", "name", "total_students")[:10]
        )
        max_s = top_qs[0]["total_students"] if top_qs.exists() else 1
        top_centers = [
            {
                "id": str(c["id"]),
                "name": c["name"],
                "students": c["total_students"],
                "percentage": round(c["total_students"] / max_s * 100) if max_s else 0,
            }
            for c in top_qs
        ]

        recent_qs = Center.objects.order_by("-created_at").values("id", "name", "created_at", "status")[:5]
        recent_activities = [
            {
                "id": f"act_{c['id']}",
                "center_name": c["name"],
                "created_at": c["created_at"].isoformat() if c["created_at"] else None,
                "status": c["status"],
            }
            for c in recent_qs
        ]

        return Response(
            {
                "status": "success",
                "data": {
                    "kpi": {
                        "centers": {
                            "active": centers_agg["active"] or 0,
                            "total": centers_agg["total"] or 0,
                        },
                        "students": {
                            "new_this_month": students_agg["new_this_month"] or 0,
                            "total": students_agg["total"] or 0,
                        },
                        "revenue": {
                            "total_this_month": int(revenue_this),
                            "percentage_change": pct_change,
                            "is_up": pct_change >= 0,
                        },
                        "subscriptions": {
                            "trial": subs_agg["trial"] or 0,
                            "pro": subs_agg["pro"] or 0,
                            "enterprise": subs_agg["enterprise"] or 0,
                            "total": centers_agg["active"] or 0,
                        },
                        "tickets": {
                            "open": open_tickets,
                        },
                    },
                    "charts": {
                        "revenue_12m": revenue_12m,
                        "student_growth": student_growth,
                        "center_distribution": center_distribution,
                        "top_centers": top_centers,
                    },
                    "recent_activities": recent_activities,
                },
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["SuperAdminDirector"])
class SuperAdminDirectorListCreateView(ListCreateAPIView):
    queryset = User.objects.filter(role=User.Role.DIRECTOR, is_deleted=False)
    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorCreateUpdateSerializer
        return DirectorListSerializer


@extend_schema(tags=["SuperAdminDirector"])
class SuperAdminDirectorDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.filter(role=User.Role.DIRECTOR, is_deleted=False)
    permission_classes = [IsSuperAdmin]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return DirectorCreateUpdateSerializer
        return DirectorListSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.is_active = False
        instance.phone = f"{instance.phone}_del_{instance.id.hex[:4]}"
        instance.save()


@extend_schema(tags=["SuperAdminCenter"])
class SuperAdminCenterStudentListView(ListAPIView):
    queryset = Center.objects.annotate(
        total_students_count=Count("students", distinct=True),
        active_students_count=Count("students", filter=Q(students__status="active"), distinct=True),
    ).order_by("id")

    permission_classes = [IsSuperAdmin]
    serializer_class = CenterStudentCountSerializer
    pagination_class = CustomPagination


@extend_schema(tags=["SuperAdminCenter"])
class SuperAdminCenterListCreateView(ListCreateAPIView):
    queryset = (
        Center.objects.select_related("director")
        .annotate(students_count=Count("students", distinct=True))
        .order_by("id")
    )
    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CenterListSerializer


@extend_schema(tags=["SuperAdminCenter"])
class SuperAdminCenterDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Center.objects.annotate(
        students_count=Count("students", distinct=True),
        teachers_count=Count("teachers", distinct=True),
    )
    permission_classes = [IsSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CenterDetailSerializer


@extend_schema(tags=["SuperAdminStudent"])
class SuperAdminStudentListCreateView(ListCreateAPIView):
    queryset = Student.objects.select_related("user", "center", "parent__user").filter(user__is_deleted=False)

    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "center"]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__phone",
        "user__email",
    ]
    ordering_fields = ["enrolled_at", "status", "user__first_name"]
    ordering = ["-enrolled_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StudentCreateUpdateSerializer
        return StudentListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(StudentDetailSerializer(student).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["SuperAdminStudent"])
class SuperAdminStudentDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.select_related("user", "center", "parent__user").filter(user__is_deleted=False)
    permission_classes = [IsSuperAdmin]
    http_method_names = ["get", "patch", "delete"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return StudentCreateUpdateSerializer
        return StudentDetailSerializer

    def perform_destroy(self, instance):
        user = instance.user
        user.is_deleted = True
        user.is_active = False
        user.phone = f"{user.phone}_del_{user.id.hex[:4]}"
        user.save()

        instance.delete()
