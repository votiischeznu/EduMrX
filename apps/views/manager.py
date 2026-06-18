from datetime import date
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions import IsManager
from apps.models.profiles import Student, Teacher
from apps.models.groups import Group, Room
from apps.models.courses import Course, Lesson, Attendance
from apps.models.payments import Payment, Debt

from apps.serializers import (
    DirectorRoomSerializer,
    DirectorCourseSerializer,
    DirectorGroupListSerializer,
    DirectorGroupDetailSerializer,
    DirectorGroupEnrollSerializer,
    DirectorLessonListSerializer,
    DirectorLessonCreateSerializer,
    DirectorAttendanceSerializer,
    DirectorAttendanceBulkSerializer,
    ManagerStudentListSerializer,
    ManagerStudentDetailSerializer,
    ManagerStudentCreateSerializer,
    ManagerTeacherListSerializer,
    ManagerTeacherDetailSerializer,
    ManagerTeacherCreateSerializer,
    ManagerGroupCreateSerializer,
    ManagerPaymentSerializer,
)


def get_manager_center_or_404(user):
    if hasattr(user, "manager_profile") and user.manager_profile.center:
        return user.manager_profile.center
    elif hasattr(user, "center") and user.center:
        return user.center
    raise NotFound("Sizga biriktirilgan faol o'quv markazi topilmadi.")


# ─── DASHBOARD ───
@extend_schema(tags=["Manager – Dashboard"])
class ManagerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        center = get_manager_center_or_404(request.user)
        today = date.today()

        students_count = Student.objects.filter(
            center=center, user__is_deleted=False
        ).count()
        teachers_count = Teacher.objects.filter(
            center=center, user__is_deleted=False
        ).count()
        groups_count = Group.objects.filter(center=center).count()

        payments_sum = (
            Payment.objects.filter(
                student__center=center,
                paid_at__year=today.year,
                paid_at__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        debts_sum = (
            Debt.objects.filter(
                student__center=center,
                created_at__year=today.year,
                created_at__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        return Response(
            {
                "center": {"id": center.id, "name": center.name},
                "statistics": {
                    "total_students": students_count,
                    "total_teachers": teachers_count,
                    "total_groups": groups_count,
                },
                "finance_this_month": {
                    "total_payments": float(payments_sum),
                    "total_debts": float(debts_sum),
                },
            }
        )


@extend_schema(tags=["Manager – Students"])
class ManagerStudentListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering = ["-created_at"]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Student.objects.filter(
            center=center, user__is_deleted=False
        ).select_related("user")

    def get_serializer_class(self):
        return (
            ManagerStudentCreateSerializer
            if self.request.method == "POST"
            else ManagerStudentListSerializer
        )

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerStudentCreateSerializer(
            data=request.data, context={"center": center}
        )
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(
            ManagerStudentDetailSerializer(student).data, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Manager – Students"])
class ManagerStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Student.objects.filter(center=center, user__is_deleted=False)

    def get_serializer_class(self):
        return (
            ManagerStudentCreateSerializer
            if self.request.method == "PATCH"
            else ManagerStudentDetailSerializer
        )

    def patch(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        instance = self.get_object()
        serializer = ManagerStudentCreateSerializer(
            instance, data=request.data, partial=True, context={"center": center}
        )
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(ManagerStudentDetailSerializer(student).data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── TEACHERS ───
@extend_schema(tags=["Manager – Teachers"])
class ManagerTeacherListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Teacher.objects.filter(
            center=center, user__is_deleted=False
        ).select_related("user")

    def get_serializer_class(self):
        return (
            ManagerTeacherCreateSerializer
            if self.request.method == "POST"
            else ManagerTeacherListSerializer
        )

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerTeacherCreateSerializer(
            data=request.data, context={"center": center}
        )
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(
            ManagerTeacherDetailSerializer(teacher).data, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Manager – Teachers"])
class ManagerTeacherDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Teacher.objects.filter(center=center, user__is_deleted=False)

    def get_serializer_class(self):
        return (
            ManagerTeacherCreateSerializer
            if self.request.method == "PATCH"
            else ManagerTeacherDetailSerializer
        )

    def patch(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        instance = self.get_object()
        serializer = ManagerTeacherCreateSerializer(
            instance, data=request.data, partial=True, context={"center": center}
        )
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(ManagerTeacherDetailSerializer(teacher).data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── ROOMS ───
@extend_schema(tags=["Manager – Rooms"])
class ManagerRoomListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorRoomSerializer

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Room.objects.filter(center=center)

    def perform_create(self, serializer):
        center = get_manager_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["Manager – Rooms"])
class ManagerRoomDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorRoomSerializer

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Room.objects.filter(center=center)


# ─── COURSES ───
@extend_schema(tags=["Manager – Courses"])
class ManagerCourseListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Course.objects.filter(center=center)

    def perform_create(self, serializer):
        center = get_manager_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["Manager – Courses"])
class ManagerCourseDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Course.objects.filter(center=center)


# ─── GROUPS ───
@extend_schema(tags=["Manager – Groups"])
class ManagerGroupListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Group.objects.filter(center=center).select_related(
            "course", "teacher__user"
        )

    def get_serializer_class(self):
        return (
            ManagerGroupCreateSerializer
            if self.request.method == "POST"
            else DirectorGroupListSerializer
        )

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerGroupCreateSerializer(
            data=request.data, context={"center": center}
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(
            DirectorGroupDetailSerializer(group).data, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Manager – Groups"])
class ManagerGroupDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Group.objects.filter(center=center)

    def get_serializer_class(self):
        return (
            ManagerGroupCreateSerializer
            if self.request.method in ["PUT", "PATCH"]
            else DirectorGroupDetailSerializer
        )


@extend_schema(tags=["Manager – Groups"])
class ManagerGroupEnrollView(CreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorGroupEnrollSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        try:
            group = Group.objects.get(pk=kwargs.get("pk"), center=center)
        except Group.DoesNotExist:
            raise NotFound("Guruh topilmadi.")

        serializer = self.get_serializer(
            data=request.data, context={"group": group, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Talabalar guruhga qo'shildi."}, status=status.HTTP_200_OK
        )


# ─── LESSONS & ATTENDANCE ───
@extend_schema(tags=["Manager – Lessons"])
class ManagerLessonListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Lesson.objects.filter(group__center=center).select_related(
            "group", "room"
        )

    def get_serializer_class(self):
        return (
            DirectorLessonCreateSerializer
            if self.request.method == "POST"
            else DirectorLessonListSerializer
        )

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = DirectorLessonCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["group"].center != center:
            raise ValidationError("Siz boshqa markaz guruhiga dars qo'sha olmaysiz.")

        lesson = serializer.save()
        return Response(
            DirectorLessonListSerializer(lesson).data, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Manager – Lessons"])
class ManagerLessonDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Lesson.objects.filter(group__center=center)

    def get_serializer_class(self):
        return (
            DirectorLessonCreateSerializer
            if self.request.method in ["PUT", "PATCH"]
            else DirectorLessonListSerializer
        )


@extend_schema(tags=["Manager – Attendance"])
class ManagerAttendanceView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def _get_lesson(self, pk):
        center = get_manager_center_or_404(self.request.user)
        try:
            return Lesson.objects.get(pk=pk, group__center=center)
        except Lesson.DoesNotExist:
            raise NotFound("Dars topilmadi.")

    def get(self, request, pk):
        lesson = self._get_lesson(pk)
        attendances = Attendance.objects.filter(lesson=lesson).select_related(
            "student__user"
        )
        return Response(DirectorAttendanceSerializer(attendances, many=True).data)

    def post(self, request, pk):
        lesson = self._get_lesson(pk)
        serializer = DirectorAttendanceBulkSerializer(
            data=request.data, context={"request": request, "lesson": lesson}
        )
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        return Response(DirectorAttendanceSerializer(results, many=True).data)


# ─── PAYMENTS ───
@extend_schema(tags=["Manager – Payments"])
class ManagerPaymentListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = (
        ManagerPaymentSerializer  # Bu yerda o'zimiz yaratgan serializer ishlatildi
    )

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Payment.objects.filter(student__center=center).order_by("-paid_at")
