from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from apps.pagination import StudentPagination
from apps.serializers.users import StudentListSerializer
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from apps.models import Student
from apps.serializers.users import StudentDetailSerializer



class StudentListView(ListAPIView):
    serializer_class = StudentListSerializer
    pagination_class = StudentPagination
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["user__first_name", "user__last_name", "user__phone", "user__email"]
    ordering_fields = ["enrolled_at", "status", "user__first_name"]
    ordering = ["-enrolled_at"]

    def get_queryset(self):
        user = self.request.user

        qs = (
            Student.objects
            .select_related("user", "center", "parent__user")
            .filter(center__status="active")
        )

        if user.is_super_admin:
            return qs

        if user.is_director:
            return qs.filter(center__director=user)

        if user.is_admin:
            return qs.filter(center__staff_members__user=user)

        if user.is_teacher:
            return qs.filter(
                enrollments__group__teacher__user=user
            ).distinct()

        return Student.objects.none()




class StudentDetailView(RetrieveAPIView):
    """
    GET /api/v1/students/<uuid:pk>
    """
    serializer_class   = StudentDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = (
            Student.objects
            .select_related("user", "center", "parent__user")
        )

        if user.is_super_admin:
            return qs

        if user.is_director:
            return qs.filter(center__director=user)

        if user.is_admin:
            return qs.filter(center__staff_members__user=user)

        if user.is_teacher:
            return qs.filter(
                enrollments__group__teacher__user=user
            ).distinct()
        return Student.objects.none()