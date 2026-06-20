from datetime import date
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions import IsManager
from apps.models import Student, Teacher, Group, Room, Course, Lesson, Attendance, Payment, Debt
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


@extend_schema(tags=["ManagerDashboard"])
class ManagerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        center = get_manager_center_or_404(request.user)
        today = date.today()

        students_count = Student.objects.filter(center=center, user__is_deleted=False).count()
        teachers_count = Teacher.objects.filter(center=center, user__is_deleted=False).count()
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


@extend_schema(tags=["ManagerStudents"])
class ManagerStudentListCreateView(ListCreateAPIView):
    queryset = Student.objects.select_related("user", "center", "parent__user")
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
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagerStudentCreateSerializer
        else:
            return ManagerStudentListSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerStudentCreateSerializer(data=request.data, context={"center": center})
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(ManagerStudentDetailSerializer(student).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerStudents"])
class ManagerStudentDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ManagerStudentCreateSerializer
        else:
            return ManagerStudentDetailSerializer

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
@extend_schema(tags=["ManagerTeachers"])
class ManagerTeacherListCreateView(ListCreateAPIView):
    queryset = Teacher.objects.select_related("user")
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center, user__is_deleted=False)

    def get_serializer_class(self):
        return ManagerTeacherCreateSerializer if self.request.method == "POST" else ManagerTeacherListSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = ManagerTeacherCreateSerializer(data=request.data, context={"center": center})
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(ManagerTeacherDetailSerializer(teacher).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerTeachers"])
class ManagerTeacherDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Teacher.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center, user__is_deleted=False)

    def get_serializer_class(self):
        return ManagerTeacherCreateSerializer if self.request.method == "PATCH" else ManagerTeacherDetailSerializer

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
@extend_schema(tags=["ManagerRooms"])
class ManagerRoomListCreateView(ListCreateAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorRoomSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center)

    def perform_create(self, serializer):
        center = get_manager_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["ManagerRooms"])
class ManagerRoomDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorRoomSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center)


# ─── COURSES ───
@extend_schema(tags=["ManagerCourses"])
class ManagerCourseListCreateView(ListCreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center)

    def perform_create(self, serializer):
        center = get_manager_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["ManagerCourses"])
class ManagerCourseDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center)


# ─── GROUPS ───
@extend_schema(tags=["ManagerGroups"])
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


@extend_schema(tags=["ManagerGroups"])
class ManagerGroupDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(center=center)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ManagerGroupCreateSerializer
        else:
            return DirectorGroupDetailSerializer


@extend_schema(tags=["ManagerGroups"])
class ManagerGroupEnrollView(CreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorGroupEnrollSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        try:
            group = Group.objects.get(pk=kwargs.get("pk"), center=center)
        except Group.DoesNotExist:
            raise NotFound("Guruh topilmadi.")

        serializer = self.get_serializer(data=request.data, context={"group": group, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Talabalar guruhga qo'shildi."}, status=status.HTTP_200_OK)


@extend_schema(tags=["ManagerLessons"])
class ManagerLessonListCreateView(ListCreateAPIView):
    queryset = Lesson.objects.select_related("group", "room")
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(group__center=center)

    def get_serializer_class(self):
        return DirectorLessonCreateSerializer if self.request.method == "POST" else DirectorLessonListSerializer

    def post(self, request, *args, **kwargs):
        center = get_manager_center_or_404(request.user)
        serializer = DirectorLessonCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["group"].center != center:
            raise ValidationError("Siz boshqa markaz guruhiga dars qo'sha olmaysiz.")

        lesson = serializer.save()
        return Response(DirectorLessonListSerializer(lesson).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerLessons"])
class ManagerLessonDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        center = get_manager_center_or_404(self.request.user)
        return qs.filter(group__center=center)

    def get_serializer_class(self):
        return (
            DirectorLessonCreateSerializer if self.request.method in ["PUT", "PATCH"] else DirectorLessonListSerializer
        )


@extend_schema(tags=["ManagerAttendance"])
class ManagerAttendanceView(APIView):
    serializer_class = DirectorAttendanceSerializer
    permission_classes = [IsAuthenticated, IsManager]

    def _get_lesson(self, pk):
        center = get_manager_center_or_404(self.request.user)
        try:
            return Lesson.objects.get(pk=pk, group__center=center)
        except Lesson.DoesNotExist:
            raise NotFound("Dars topilmadi.")

    def get(self, request, pk):
        lesson = self._get_lesson(pk)
        attendances = Attendance.objects.filter(lesson=lesson).select_related("student__user")
        return Response(self.serializer_class(attendances, many=True).data)

    def post(self, request, pk):
        lesson = self._get_lesson(pk)
        serializer = DirectorAttendanceBulkSerializer(data=request.data, context={"request": request, "lesson": lesson})
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        return Response(self.serializer_class(results, many=True).data)


# ─── PAYMENTS ───
@extend_schema(tags=["ManagerPayments"])
class ManagerPaymentListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = ManagerPaymentSerializer

    def get_queryset(self):
        center = get_manager_center_or_404(self.request.user)
        return Payment.objects.filter(student__center=center).order_by("-paid_at")
