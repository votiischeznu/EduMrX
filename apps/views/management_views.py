from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.models import Student, Teacher, Attendance
from apps.pagination import StudentPagination
from apps.serializers import (
    StudentListSerializer, StudentDetailSerializer, AttendanceSerializer, TeacherDetailSerializer,
    TeacherListSerializer, StudentCreateUpdateSerializer, TeacherCreateUpdateSerializer)


@extend_schema(tags=['ManagementStudent'])
class ManagementStudentListCreateView(ListCreateAPIView):
    pagination_class = StudentPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone", "user__email"]
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


@extend_schema(tags=['ManagementStudent'])
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
        fresh_student = Student.objects.for_user(request.user).get(pk=student_instance.pk)
        return Response(
            self.get_serializer(fresh_student).data
        )


@extend_schema(tags=['ManagementTeacher'])
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

        if user.is_super_admin: return qs
        if user.is_director: return qs.filter(centers__director=user)
        if user.is_admin: return qs.filter(centers__staff_members__user=user)
        if user.is_student:
            return qs.filter(teaching_groups__enrollments__student__user=user).distinct()

        return Teacher.objects.none()


@extend_schema(tags=['ManagementTeacher'])
class ManagementTeacherDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return TeacherCreateUpdateSerializer
        return TeacherDetailSerializer

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
        lesson = serializer.validated_data["lesson"]
        center = lesson.group.center

        if user.is_super_admin:
            pass
        elif user.is_director:
            if center.director != user:
                raise PermissionDenied("Bu dars sizning markazingizga tegishli emas.")
        elif user.is_admin:
            if not center.staff_members.filter(user=user).exists():
                raise PermissionDenied("Siz ushbu markaz darslariga davomat qila olmaysiz.")
        elif user.is_teacher:
            if lesson.group.teacher.user != user:
                raise PermissionDenied("Siz faqat o'zingiz dars o'tadigan guruhga davomat qila olasiz.")
        else:
            raise PermissionDenied("Sizda davomat olish huquqi yo'q.")

        serializer.save()
