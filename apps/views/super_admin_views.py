from django.db.models import Count, Sum, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Student, Center, User, Payment
from apps.pagination import CustomPagination
from apps.permissions import IsSuperAdmin
from apps.serializers import SuperAdminMenuStatsSerializer, DirectorCreateUpdateSerializer, DirectorListSerializer, \
    CenterListSerializer, CenterStudentCountSerializer, CenterDetailSerializer, StudentCreateUpdateSerializer, \
    StudentDetailSerializer, StudentListSerializer


@extend_schema(tags=['SuperAdminDashboard'])
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


@extend_schema(tags=['SuperAdminDirector'])
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


@extend_schema(tags=['SuperAdminDirector'])
class SuperAdminDirectorDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.DIRECTOR, is_deleted=False)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return DirectorCreateUpdateSerializer
        return DirectorListSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.is_active = False
        instance.phone = f"{instance.phone}_del_{instance.id.hex[:4]}"
        instance.save()


@extend_schema(tags=['SuperAdminStudent'])
class SuperAdminStudentCenterListView(ListAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = CenterStudentCountSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return Center.objects.annotate(
            total_students_count=Count("students", distinct=True),
            active_students_count=Count("students", filter=Q(students__status="active"), distinct=True)
        ).order_by('id')


@extend_schema(tags=['SuperAdminCenter'])
class SuperAdminCenterListCreateView(ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CenterListSerializer

    def get_queryset(self):
        return Center.objects.select_related("director").annotate(
            students_count=Count("students", distinct=True)
        ).order_by('id')


@extend_schema(tags=['SuperAdminCenter'])
class SuperAdminCenterDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CenterDetailSerializer

    def get_queryset(self):
        return Center.objects.annotate(
            students_count=Count("students", distinct=True),
            teachers_count=Count("teachers", distinct=True)
        )

@extend_schema(tags=['SuperAdminStudent'])
class SuperAdminStudentListCreateView(ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone", "user__email"]
    ordering_fields = ["enrolled_at", "status", "user__first_name"]
    ordering = ["-enrolled_at"]

    def get_queryset(self):
        return Student.objects.select_related(
            "user", "center", "parent__user"
        ).filter(user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StudentCreateUpdateSerializer
        return StudentListSerializer

    def create(self, request, *args, **kwargs):
        serializer = StudentCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(
            StudentDetailSerializer(student).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=['SuperAdminStudent'])
class SuperAdminStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        return Student.objects.select_related(
            "user", "center", "parent__user"
        ).filter(user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return StudentCreateUpdateSerializer
        return StudentDetailSerializer

    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()  # → Student.delete() total_students kamaytiradi
        user.is_deleted = True
        user.is_active = False
        user.phone = f"{user.phone}_del_{user.id.hex[:4]}"
        user.save()
