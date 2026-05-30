from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


from apps.pagination import StudentPagination
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from apps.models import Student, Teacher, Attendance
from apps.permissions import IsSuperAdmin
from apps.serializers import (
    StudentListSerializer, StudentDetailSerializer, AttendanceSerializer, TeacherDetailSerializer, TeacherListSerializer)
from apps.serializers.management_serializers import StudentCreateUpdateSerializer, TeacherCreateUpdateSerializer


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
