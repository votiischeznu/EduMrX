from datetime import date
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions import IsManager
from apps.models import Student, Teacher, Group, Room, Course, Lesson, Attendance, Payment, Debt
from apps.serializers import (
    DirectorRoomSerializer,
    DirectorCourseSerializer,
    DirectorGroupListSerializer,
    DirectorGroupEnrollSerializer,
    DirectorLessonListSerializer,
    DirectorLessonCreateSerializer,
    DirectorAttendanceSerializer,
    DirectorAttendanceBulkSerializer,
    DirectorGroupCreateSerializer,
    ManagerStudentListSerializer,
    ManagerStudentDetailSerializer,
    ManagerStudentCreateSerializer,
    ManagerTeacherListSerializer,
    ManagerTeacherDetailSerializer,
    ManagerTeacherCreateSerializer,
    ManagerGroupCreateSerializer,
    ManagerPaymentSerializer,
)


def get_manager_branch_or_404(user):
    staff_profile = getattr(user, "staff_profile", None)
    if staff_profile is None or not staff_profile.center_id:
        raise NotFound("Sizga biriktirilgan faol o'quv markazi topilmadi.")
    if not staff_profile.branch_id:
        raise NotFound("Sizga biriktirilgan faol filial topilmadi.")
    return staff_profile.center, staff_profile.branch


@extend_schema(tags=["ManagerDashboard"])
class ManagerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        center, branch = get_manager_branch_or_404(request.user)
        today = date.today()

        students_count = Student.objects.filter(
            center=center, branch=branch, user__is_deleted=False
        ).count()
        teachers_count = Teacher.objects.filter(
            centers=center, branch=branch, user__is_deleted=False
        ).count()
        groups_count = Group.objects.filter(center=center, branch=branch).count()

        payments_sum = (
            Payment.objects.filter(
                student__center=center,
                branch=branch,
                paid_at__year=today.year,
                paid_at__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        debts_sum = (
            Debt.objects.filter(
                student__center=center,
                student__branch=branch,
                created_at__year=today.year,
                created_at__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        return Response(
            {
                "center": {"id": center.id, "name": center.name},
                "branch": {"id": branch.id, "name": branch.name},
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
    queryset = Student.objects.select_related("user", "center", "branch", "parent__user")
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
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(center=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagerStudentCreateSerializer
        else:
            return ManagerStudentListSerializer

    def post(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = ManagerStudentCreateSerializer(
            data=request.data, context={"center": center, "branch": branch}
        )
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
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(center=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ManagerStudentCreateSerializer
        else:
            return ManagerStudentDetailSerializer

    def patch(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        instance = self.get_object()
        serializer = ManagerStudentCreateSerializer(
            instance, data=request.data, partial=True, context={"center": center, "branch": branch}
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
    queryset = Teacher.objects.select_related("user", "centers", "branch")
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]

    def get_queryset(self):
        qs = super().get_queryset()
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(centers=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        return ManagerTeacherCreateSerializer if self.request.method == "POST" else ManagerTeacherListSerializer

    def post(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = ManagerTeacherCreateSerializer(
            data=request.data, context={"center": center, "branch": branch}
        )
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
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(centers=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        return ManagerTeacherCreateSerializer if self.request.method == "PATCH" else ManagerTeacherDetailSerializer

    def patch(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        instance = self.get_object()
        serializer = ManagerTeacherCreateSerializer(
            instance, data=request.data, partial=True, context={"center": center, "branch": branch}
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
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(center=center, branch=branch)

    def perform_create(self, serializer):
        center, branch = get_manager_branch_or_404(self.request.user)
        serializer.save(center=center, branch=branch)


@extend_schema(tags=["ManagerRooms"])
class ManagerRoomDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorRoomSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(center=center, branch=branch)


# ─── COURSES ───
# Eslatma: Kurslar odatda butun markaz uchun umumiy bo'ladi (filial-agnostik),
# shuning uchun bu yerda atayin faqat `center` bo'yicha filtrlanmoqda, `branch`
# bo'yicha emas. Agar Course modelida ham branch bo'lishi kerak bo'lsa -- ayting.
@extend_schema(tags=["ManagerCourses"])
class ManagerCourseListCreateView(ListCreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        center, _branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(center=center)

    def perform_create(self, serializer):
        center, _branch = get_manager_branch_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["ManagerCourses"])
class ManagerCourseDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        center, _branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(center=center)


# ─── GROUPS ───
@extend_schema(tags=["ManagerGroups"])
class ManagerGroupListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return Group.objects.filter(center=center, branch=branch).select_related(
            "course", "teacher__user", "branch"
        )

    def get_serializer_class(self):
        return ManagerGroupCreateSerializer if self.request.method == "POST" else DirectorGroupListSerializer

    def post(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = ManagerGroupCreateSerializer(
            data=request.data, context={"center": center, "branch": branch}
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(DirectorGroupCreateSerializer(group).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerGroups"])
class ManagerGroupDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(center=center, branch=branch)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ManagerGroupCreateSerializer
        else:
            return DirectorGroupCreateSerializer


@extend_schema(tags=["ManagerGroups"])
class ManagerGroupEnrollView(CreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorGroupEnrollSerializer

    def post(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        try:
            group = Group.objects.get(pk=kwargs.get("pk"), center=center, branch=branch)
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
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(group__center=center, group__branch=branch)

    def get_serializer_class(self):
        return DirectorLessonCreateSerializer if self.request.method == "POST" else DirectorLessonListSerializer

    def post(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = DirectorLessonCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        group = serializer.validated_data["group"]
        if group.center_id != center.id or group.branch_id != branch.id:
            raise ValidationError("Siz boshqa filial guruhiga dars qo'sha olmaysiz.")

        lesson = serializer.save()
        return Response(DirectorLessonListSerializer(lesson).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerLessons"])
class ManagerLessonDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        qs = super().get_queryset()
        center, branch = get_manager_branch_or_404(self.request.user)
        return qs.filter(group__center=center, group__branch=branch)

    def get_serializer_class(self):
        return (
            DirectorLessonCreateSerializer if self.request.method in ["PUT", "PATCH"] else DirectorLessonListSerializer
        )


@extend_schema(tags=["ManagerAttendance"])
class ManagerAttendanceView(APIView):
    serializer_class = DirectorAttendanceSerializer
    permission_classes = [IsAuthenticated, IsManager]

    def _get_lesson(self, pk):
        center, branch = get_manager_branch_or_404(self.request.user)
        try:
            return Lesson.objects.get(pk=pk, group__center=center, group__branch=branch)
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
# Eslatma: bu faqat RO'YXAT ko'rsatish uchun (ListAPIView). To'lov SERIALIZER
# "student" maydoni read_only nested bo'lgani uchun avvalgi ListCreateAPIView
# POST so'rovida ishlamas edi (student bog'lanmagan holda saqlashga urinib,
# IntegrityError berardi). Agar Manager to'lov ham YOZA olishi kerak bo'lsa,
# alohida write-serializer (masalan ManagerPaymentCreateSerializer, student=UUIDField)
# yozish kerak -- buni alohida so'rab oling.
@extend_schema(tags=["ManagerPayments"])
class ManagerPaymentListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = ManagerPaymentSerializer

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return Payment.objects.filter(
            student__center=center, branch=branch
        ).select_related("student__user").order_by("-paid_at")