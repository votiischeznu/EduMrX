from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.permissions import IsManager
from apps.models.profiles import Student, Teacher
from apps.models.groups import Group
from apps.models.courses import Course
from apps.models.payments import Payment

from apps.serializers.director import (
    DirectorCourseSerializer,
    DirectorGroupListSerializer,
    DirectorGroupDetailSerializer,
)
from apps.serializers.manager import (
    ManagerStudentListSerializer, ManagerStudentDetailSerializer, ManagerStudentCreateSerializer,
    ManagerTeacherListSerializer, ManagerTeacherDetailSerializer, ManagerTeacherCreateSerializer,
    ManagerGroupCreateSerializer
)

def get_manager_center_or_404(user):
    if hasattr(user, 'manager_profile') and user.manager_profile.center:
        return user.manager_profile.center
    elif hasattr(user, 'center') and user.center:
        return user.center
    raise NotFound("Sizga biriktirilgan faol o'quv markazi topilmadi.")


@extend_schema(tags=["Manager – Students"])
class ManagerStudentListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering = ["-created_at"]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Student.objects.filter(center=center, user__is_deleted=False).select_related("user")

    def get_serializer_class(self):
        return ManagerStudentCreateSerializer if self.request.method == "POST" else ManagerStudentListSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerStudentCreateSerializer(data=request.data, context={"request": request, "center": center})
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(ManagerStudentDetailSerializer(student).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Manager – Students"])
class ManagerStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Student.objects.filter(center=center, user__is_deleted=False)

    def get_serializer_class(self):
        return ManagerStudentCreateSerializer if self.request.method == "PATCH" else ManagerStudentDetailSerializer

    def patch(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        instance = self.get_object()
        serializer = ManagerStudentCreateSerializer(instance, data=request.data, partial=True, context={"center": center})
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(ManagerStudentDetailSerializer(student).data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Manager – Teachers"])
class ManagerTeacherListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Teacher.objects.filter(center=center, user__is_deleted=False).select_related("user")

    def get_serializer_class(self):
        return ManagerTeacherCreateSerializer if self.request.method == "POST" else ManagerTeacherListSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerTeacherCreateSerializer(data=request.data, context={"center": center})
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(ManagerTeacherDetailSerializer(teacher).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Manager – Courses"])
class ManagerCourseListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Course.objects.filter(center=center)

    def perform_create(self, serializer):
        center = get_manager_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["Manager – Groups"])
class ManagerGroupListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Group.objects.filter(center=center).select_related("course", "teacher__user")

    def get_serializer_class(self):
        return ManagerGroupCreateSerializer if self.request.method == "POST" else DirectorGroupListSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerGroupCreateSerializer(data=request.data, context={"center": center})
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(DirectorGroupDetailSerializer(group).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Manager – Payments"])
class ManagerPaymentListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Payment.objects.filter(student__center=center).order_by("-paid_at")