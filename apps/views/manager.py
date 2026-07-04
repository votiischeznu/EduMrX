from datetime import date

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Attendance, Course, Debt, Group, Lesson, Payment, Room, Student, Teacher
from apps.permissions import IsManager
from apps.serializers import (
    DirectorAttendanceBulkSerializer,
    DirectorAttendanceSerializer,
    DirectorCourseSerializer,
    DirectorGroupCreateSerializer,
    DirectorGroupEnrollSerializer,
    DirectorGroupListSerializer,
    DirectorLessonCreateSerializer,
    DirectorLessonListSerializer,
    DirectorRoomSerializer,
    ManagerGroupCreateSerializer,
    ManagerPaymentSerializer,
    ManagerStudentCreateSerializer,
    ManagerStudentDetailSerializer,
    ManagerStudentListSerializer,
    ManagerTeacherCreateSerializer,
    ManagerTeacherDetailSerializer,
    ManagerTeacherListSerializer,
)


def get_manager_branch_or_404(user):
    staff_profile = getattr(user, "staff_profile", None)
    if staff_profile is None or not staff_profile.center_id:
        raise NotFound("Sizga biriktirilgan faol o'quv markazi topilmadi.")
    if not staff_profile.branch_id:
        raise NotFound("Sizga biriktirilgan faol filial topilmadi.")
    return staff_profile.center, staff_profile.branch


# ==========================================
# DASHBOARD
# ==========================================
@extend_schema(tags=["ManagerDashboard"])
class ManagerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        center, branch = get_manager_branch_or_404(request.user)
        today = date.today()

        students_count = Student.objects.filter(center=center, branch=branch, user__is_deleted=False).count()
        teachers_count = Teacher.objects.filter(centers=center, branch=branch, user__is_deleted=False).count()
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
        # FIX: Debt modeli BaseModel'dan meros oladi va created_at maydoniga ega
        # emas (faqat due_date bor). Avval created_at__year/month ishlatilgani
        # uchun FieldError bilan yiqilardi. due_date bilan almashtirildi.
        debts_sum = (
            Debt.objects.filter(
                student__center=center,
                student__branch=branch,
                due_date__year=today.year,
                due_date__month=today.month,
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


# ==========================================
# STUDENTS
# ==========================================
@extend_schema(tags=["ManagerStudents"])
class ManagerStudentListCreateView(ListCreateAPIView):
    queryset = Student.objects.select_related("user", "center", "branch", "parent__user")
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering = ["-created_at"]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(center=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagerStudentCreateSerializer
        return ManagerStudentListSerializer

    def create(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = self.get_serializer(data=request.data, context={"center": center, "branch": branch})
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(ManagerStudentDetailSerializer(student).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerStudents"])
class ManagerStudentDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(center=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ManagerStudentCreateSerializer
        return ManagerStudentDetailSerializer

    # ESLATMA: bu yerda context ("center"/"branch") is_valid()dan KEYIN
    # o'rnatilsa ham xato bermaydi, chunki ManagerStudentCreateSerializer'ning
    # validate_phone/validate_email metodlari context'ga emas, self.instance'ga
    # tayanadi. Shunga qaramay, Group bilan bo'lgan xatoni takrorlamaslik uchun
    # xavfsizlik maqsadida context'ni is_valid()dan OLDIN o'rnatamiz.
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        center, branch = get_manager_branch_or_404(request.user)
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context={**self.get_serializer_context(), "center": center, "branch": branch},
        )
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(ManagerStudentDetailSerializer(student).data)

    def perform_destroy(self, instance):
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])


# ==========================================
# TEACHERS
# ==========================================
@extend_schema(tags=["ManagerTeachers"])
class ManagerTeacherListCreateView(ListCreateAPIView):
    queryset = Teacher.objects.select_related("user", "branch")
    permission_classes = [IsAuthenticated, IsManager]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(centers=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagerTeacherCreateSerializer
        return ManagerTeacherListSerializer

    def create(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = self.get_serializer(data=request.data, context={"center": center, "branch": branch})
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(ManagerTeacherDetailSerializer(teacher).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerTeachers"])
class ManagerTeacherDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Teacher.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(centers=center, branch=branch, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ManagerTeacherCreateSerializer
        return ManagerTeacherDetailSerializer

    # ESLATMA: Student bilan bir xil sabab -- xavfsizlik uchun context oldindan.
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        center, branch = get_manager_branch_or_404(request.user)
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context={**self.get_serializer_context(), "center": center, "branch": branch},
        )
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(ManagerTeacherDetailSerializer(teacher).data)

    def perform_destroy(self, instance):
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])


# ==========================================
# ROOMS
# ==========================================
@extend_schema(tags=["ManagerRooms"])
class ManagerRoomListCreateView(ListCreateAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorRoomSerializer

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(center=center, branch=branch)

    def perform_create(self, serializer):
        center, branch = get_manager_branch_or_404(self.request.user)
        serializer.save(center=center, branch=branch)


@extend_schema(tags=["ManagerRooms"])
class ManagerRoomDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorRoomSerializer

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(center=center, branch=branch)


# ==========================================
# COURSES
# ==========================================
@extend_schema(tags=["ManagerCourses"])
class ManagerCourseListCreateView(ListCreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        center, _ = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(center=center)

    def perform_create(self, serializer):
        center, _ = get_manager_branch_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["ManagerCourses"])
class ManagerCourseDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = DirectorCourseSerializer

    def get_queryset(self):
        center, _ = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(center=center)


# ==========================================
# GROUPS
# ==========================================
@extend_schema(tags=["ManagerGroups"])
class ManagerGroupListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return Group.objects.filter(center=center, branch=branch).select_related("course", "teacher__user", "branch")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagerGroupCreateSerializer
        return DirectorGroupListSerializer

    def create(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = self.get_serializer(data=request.data, context={"center": center, "branch": branch})
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(DirectorGroupCreateSerializer(group).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["ManagerGroups"])
class ManagerGroupDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(center=center, branch=branch)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ManagerGroupCreateSerializer
        return DirectorGroupCreateSerializer

    # FIX: Avval `update()` ichida `serializer.is_valid(raise_exception=True)`
    # chaqirilgandan KEYIN `perform_update()` orqali context["center"]/["branch"]
    # o'rnatilardi. ManagerGroupCreateSerializer.validate() esa aynan
    # is_valid() paytida ishlaydi va context.get("center")ni o'qiydi -- demak
    # u doim None edi. Natijada:
    #   - to'liq payload yuborilsa ham "Kurs/O'qituvchi/Xona topilmadi" (400),
    #     chunki Course.objects.filter(center=None) hech narsa topmaydi;
    #   - partial PATCH'da lesson_start_time/lesson_end_time yuborilmasa,
    #     ularni solishtirish TypeError (500) berardi.
    # Yechim: center/branch'ni serializer yaratilishidan OLDIN, bitta joyda
    # context sifatida beramiz, keyin is_valid() chaqiramiz.
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        center, branch = get_manager_branch_or_404(request.user)
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context={**self.get_serializer_context(), "center": center, "branch": branch},
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(DirectorGroupCreateSerializer(group).data)


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


# ==========================================
# LESSONS
# ==========================================
@extend_schema(tags=["ManagerLessons"])
class ManagerLessonListCreateView(ListCreateAPIView):
    # FIX: Lesson modelida "room" FK maydoni mavjud emas (faqat "group" bor).
    # Avval select_related("group", "room") ishlatilgani uchun har bir GET
    # so'rovida "Invalid field name(s) given in select_related: 'room'"
    # FieldError bilan yiqilardi.
    queryset = Lesson.objects.select_related("group")
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(group__center=center, group__branch=branch)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorLessonCreateSerializer
        return DirectorLessonListSerializer

    def create(self, request, *args, **kwargs):
        center, branch = get_manager_branch_or_404(request.user)
        serializer = self.get_serializer(data=request.data, context={"request": request})
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
        center, branch = get_manager_branch_or_404(self.request.user)
        return self.queryset.filter(group__center=center, group__branch=branch)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DirectorLessonCreateSerializer
        return DirectorLessonListSerializer


# ==========================================
# ATTENDANCE
# ==========================================
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


# ==========================================
# PAYMENTS
# ==========================================
@extend_schema(tags=["ManagerPayments"])
class ManagerPaymentListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = ManagerPaymentSerializer

    def get_queryset(self):
        center, branch = get_manager_branch_or_404(self.request.user)
        return (
            Payment.objects.filter(student__center=center, branch=branch)
            .select_related("student__user")
            .order_by("-paid_at")
        )