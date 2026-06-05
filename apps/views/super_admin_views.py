from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Student, Center, User, Payment
from apps.pagination import CustomPagination
from apps.permissions import IsSuperAdmin
from apps.serializers import SuperAdminMenuStatsSerializer, DirectorCreateUpdateSerializer, DirectorListSerializer, \
    CenterListSerializer, CenterStudentCountSerializer, CenterDetailSerializer


class SuperAdminDashboardView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request, *args, **kwargs):
        total_students_count = Student.objects.count()
        active_students_count = Student.objects.filter(status=Student.Status.ACTIVE).count()
        total_directors = User.objects.filter(role=User.Role.DIRECTOR, is_deleted=False).count()
        total_centers = Center.objects.count()

        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_income = Payment.objects.filter(
            status=Payment.Status.PAID,
            paid_at__gte=start_of_month
        ).aggregate(total=Sum('final_amount'))['total'] or 0

        menu_data = {
            "dashboards": {"title": "Boshqaruv paneli", "link": "/super-admin/dashboard"},
            "students": {
                "title": "Talabalar",
                "total_count": total_students_count,
                "active_count": active_students_count,
                "link": "/super-admin/students"
            },
            "directors": {"title": "Direktorlar", "total_count": total_directors, "link": "/super-admin/directors"},
            "centers": {"title": "O'quv markazlari", "total_count": total_centers, "link": "/super-admin/centers"},
            "payments": {"title": "To'lovlar", "this_month_income": float(monthly_income),
                         "link": "/super-admin/payments"}
        }
        serializer = SuperAdminMenuStatsSerializer(menu_data)
        return Response(serializer.data)


class SuperAdminDirectorListCreateView(ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.DIRECTOR, is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorCreateUpdateSerializer
        return DirectorListSerializer


class SuperAdminDirectorDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.DIRECTOR, is_deleted=False)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return DirectorCreateUpdateSerializer
        return DirectorListSerializer

    def perform_destroy(self, instance):
        # Soft delete mantiqi
        instance.is_deleted = True
        instance.is_active = False
        instance.phone = f"{instance.phone}_del_{instance.id.hex[:4]}"
        instance.save()


class SuperAdminStudentCenterListView(ListAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = CenterStudentCountSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return Center.objects.select_related("director").annotate(
            total_students_count=Count("students", distinct=True),
            active_students_count=Count("students", filter=Q(students__status="active"), distinct=True)
        )


class SuperAdminCenterListCreateView(ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CenterListSerializer

    def get_queryset(self):
        return Center.objects.select_related("director").annotate(
            students_count=Count("students", distinct=True)
        )


class SuperAdminCenterDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CenterDetailSerializer

    def get_queryset(self):
        return Center.objects.annotate(
            students_count=Count("students", distinct=True),
            teachers_count=Count("teachers", distinct=True)
        )

