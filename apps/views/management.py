from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.models import Student, Teacher, Attendance
from apps.pagination import CustomPagination
from apps.serializers import (
    StudentListSerializer,
    StudentDetailSerializer,
    AttendanceSerializer,
    TeacherDetailSerializer,
    TeacherListSerializer,
    StudentCreateUpdateSerializer,
    TeacherCreateUpdateSerializer,
)


@extend_schema(tags=["ManagementStudent"])
class ManagementStudentListCreateView(ListCreateAPIView):
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
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

    def get_queryset(self):
        return Student.objects.for_user(self.request.user).select_related(
            "user", "center", "parent__user"
        )


@extend_schema(tags=["ManagementStudent"])
class ManagementStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return StudentCreateUpdateSerializer
        return StudentDetailSerializer

    def get_queryset(self):
        return Student.objects.for_user(self.request.user).select_related(
            "user", "center", "parent__user"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_instance = serializer.save()
        fresh_student = Student.objects.for_user(request.user).get(
            pk=student_instance.pk
        )
        return Response(self.get_serializer(fresh_student).data)


@extend_schema(tags=["ManagementTeacher"])
class ManagementTeacherListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["centers", "specialization"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TeacherCreateUpdateSerializer
        return TeacherListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Teacher.objects.select_related("user", "centers")

        if user.is_super_admin:
            return qs
        if user.is_director:
            return qs.filter(centers__director=user)
        if user.is_admin:
            return qs.filter(centers__staff_members__user=user)
        if user.is_student:
            return qs.filter(
                teaching_groups__enrollments__student__user=user
            ).distinct()

        return Teacher.objects.none()


@extend_schema(tags=["ManagementTeacher"])
class ManagementTeacherDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return TeacherCreateUpdateSerializer
        return TeacherDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Teacher.objects.select_related("user", "centers")

        if user.is_super_admin:
            return qs
        if user.is_director:
            return qs.filter(centers__director=user)
        if user.is_admin:
            return qs.filter(centers__staff_members__user=user)
        if user.is_student:
            return qs.filter(
                teaching_groups__enrollments__student__user=user
            ).distinct()

        return Teacher.objects.none()


@extend_schema(tags=["ManagementAttendance"])
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

        if user.is_super_admin:
            return qs
        if user.is_director:
            return qs.filter(lesson__group__center__director=user)
        if user.is_admin:
            return qs.filter(lesson__group__center__staff_members__user=user)
        if user.is_teacher:
            return qs.filter(lesson__group__teacher__user=user)
        if user.is_student:
            return qs.filter(student__user=user)

        return Attendance.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        lesson = serializer.validated_data["lesson"]
        center = lesson.group.center

        if user.is_super_admin:
            pass
        elif user.is_director:
            if center.director != user:
                raise PermissionDenied("Bu dars sizning markazingizga tegishli emas.")
        elif user.is_admin:
            if not center.staff_members.filter(user=user).exists():
                raise PermissionDenied(
                    "Siz ushbu markaz darslariga davomat qila olmaysiz."
                )
        elif user.is_teacher:
            if lesson.group.teacher.user != user:
                raise PermissionDenied(
                    "Siz faqat o'zingiz dars o'tadigan guruhga davomat qila olasiz."
                )
        else:
            raise PermissionDenied("Sizda davomat olish huquqi yo'q.")

        serializer.save()

    @action(detail=False, methods=["get"], url_path="overview")
    def overview(self, request):
        period = request.query_params.get("period", "this_week")

        attendance_qs = self.get_queryset()

        now = timezone.now()
        start_date = now - timedelta(days=7)
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "this_week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "this_month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        attendance_qs = attendance_qs.filter(marked_at__gte=start_date)

        stats = attendance_qs.aggregate(
            total=Count("id"),
            absent=Count("id", filter=Q(status__iexact="absent"))
            | Count("id", filter=Q(status__iexact="Kelmadi")),
        )
        total_count = stats["total"] or 0
        absent_count = stats["absent"] or 0
        present_count = total_count - absent_count

        attendance_rate = 0
        if total_count > 0:
            attendance_rate = round((present_count / total_count) * 100)

        data = {
            "absent_count": absent_count,
            "attendance_rate": attendance_rate,
            "total_count": total_count,
            "period": period,
        }

        return Response(data, status=status.HTTP_OK)
