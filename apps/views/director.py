from datetime import date

from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import TruncMonth
from rest_framework import status
from rest_framework.response import Response

from apps.models.centers import Center
from apps.models.profiles import Student
from apps.models.payments import Payment, Debt
from apps.models.groups import Group
from apps.serializers.director import (
    DirectorStudentCreateSerializer,
    DirectorStudentDetailSerializer,
    DirectorStudentListSerializer,
)


from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.exceptions import NotFound
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.models.profiles import Teacher
from apps.models.groups import Room
from apps.models.courses import Course
from apps.models.courses import Lesson, Attendance
from apps.permissions import IsDirector
from apps.serializers.director import (
    # Teachers
    DirectorTeacherCreateSerializer,
    DirectorTeacherDetailSerializer,
    DirectorTeacherListSerializer,
    # Rooms
    DirectorRoomSerializer,
    # Courses
    DirectorCourseSerializer,
    # Groups
    DirectorGroupCreateSerializer,
    DirectorGroupDetailSerializer,
    DirectorGroupEnrollSerializer,
    DirectorGroupListSerializer,
    # Lessons
    DirectorLessonCreateSerializer,
    DirectorLessonListSerializer,
    # Attendance
    DirectorAttendanceBulkSerializer,
    DirectorAttendanceSerializer,
)


def get_director_centers(user):
    return Center.objects.filter(director=user, status="active")


# ─── Dashboard ────────────────────────────────────────────────────────────────


class DirectorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    @extend_schema(tags=["1. Director"])
    def get(self, request):
        user = request.user
        center = Center.objects.filter(director=user).first()
        if not center:
            return Response(
                {"detail": "Sizga biriktirilgan markaz topilmadi."}, status=404
            )

        today = date.today()
        current_year = today.year
        current_month = today.month

        # ── KPI ──────────────────────────────────────────────────────────────
        total_students = center.students.filter(user__is_deleted=False).count()
        active_students = center.students.filter(
            status="active", user__is_deleted=False
        ).count()
        total_teachers = center.teachers.filter(user__is_deleted=False).count()
        total_groups = center.groups.count()
        active_groups = center.groups.filter(status="active").count()

        monthly_revenue = Payment.objects.filter(
            student__center=center,
            status="paid",
            period_year=current_year,
            period_month=current_month,
        ).aggregate(total=Sum("final_amount", default=0))["total"]

        total_debt = Debt.objects.filter(
            student__center=center,
            status__in=["unpaid", "partially_paid"],
        ).aggregate(total=Sum("amount", default=0))["total"]

        # ── Revenue chart (12 oy) ─────────────────────────────────────────────
        revenue_chart = (
            Payment.objects.filter(student__center=center, status="paid")
            .annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(revenue=Sum("final_amount", output_field=DecimalField()))
            .order_by("month")
        )
        chart_data = [
            {
                "month": entry["month"].strftime("%Y-%m"),
                "revenue": float(entry["revenue"]),
            }
            for entry in revenue_chart
            if entry["month"]
        ]

        # ── Group distribution ────────────────────────────────────────────────
        group_stats = center.groups.values("status").annotate(count=Count("id"))
        group_distribution = {g["status"]: g["count"] for g in group_stats}

        # ── Top 5 groups ──────────────────────────────────────────────────────
        top_groups = (
            Group.objects.filter(center=center)
            .annotate(
                revenue=Sum(
                    "payments__final_amount",
                    filter=Q(payments__status="paid"),
                    default=0,
                )
            )
            .order_by("-revenue")[:5]
            .values("id", "name", "student_count", "status", "revenue")
        )

        # ── Recent 10 payments ────────────────────────────────────────────────
        recent_payments = (
            Payment.objects.filter(student__center=center, status="paid")
            .select_related("student__user", "group")
            .order_by("-paid_at")[:10]
        )
        recent_payments_data = [
            {
                "student": p.student.full_name,
                "group": p.group.name if p.group else None,
                "amount": float(p.final_amount),
                "method": p.method,
                "paid_at": p.paid_at,
            }
            for p in recent_payments
        ]

        return Response(
            {
                "kpi": {
                    "total_students": total_students,
                    "active_students": active_students,
                    "total_teachers": total_teachers,
                    "total_groups": total_groups,
                    "active_groups": active_groups,
                    "monthly_revenue": float(monthly_revenue),
                    "total_debt": float(total_debt),
                },
                "revenue_chart": chart_data,
                "group_distribution": group_distribution,
                "top_groups": list(top_groups),
                "recent_payments": recent_payments_data,
            }
        )


# ─── Students ─────────────────────────────────────────────────────────────────


class DirectorStudentListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["enrolled_at", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Student.objects.filter(
            center__in=centers, user__is_deleted=False
        ).select_related("user", "center", "parent__user")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorStudentCreateSerializer
        return DirectorStudentListSerializer

    @extend_schema(tags=["2. Director — Students"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["2. Director — Students"])
    def post(self, request, *args, **kwargs):
        centers = get_director_centers(request.user)
        serializer = DirectorStudentCreateSerializer(
            data=request.data,
            context={"request": request, "centers": centers},
        )
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(
            DirectorStudentDetailSerializer(student).data,
            status=status.HTTP_201_CREATED,
        )


class DirectorStudentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Student.objects.filter(
            center__in=centers, user__is_deleted=False
        ).select_related("user", "center", "parent__user")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DirectorStudentCreateSerializer
        return DirectorStudentDetailSerializer

    @extend_schema(tags=["2. Director — Students"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["2. Director — Students"])
    def patch(self, request, *args, **kwargs):
        centers = get_director_centers(request.user)
        instance = self.get_object()
        serializer = DirectorStudentCreateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request, "centers": centers},
        )
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(DirectorStudentDetailSerializer(student).data)

    @extend_schema(tags=["2. Director — Students"])
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# apps/views/director.py ga QO'SHILADI
# (mavjud Student views lardan keyin)
# ============================================================


class DirectorTeacherListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["created_at", "experience"]
    ordering = ["-created_at"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Teacher.objects.filter(
            centers__in=centers, user__is_deleted=False
        ).select_related("user", "centers")

    def get_serializer_class(self):
        return (
            DirectorTeacherCreateSerializer
            if self.request.method == "POST"
            else DirectorTeacherListSerializer
        )

    @extend_schema(tags=["3. Director — Teachers"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["3. Director — Teachers"])
    def post(self, request, *args, **kwargs):
        center = get_director_centers(request.user).first()
        serializer = DirectorTeacherCreateSerializer(
            data=request.data,
            context={"request": request, "center": center},
        )
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(
            DirectorTeacherDetailSerializer(teacher).data,
            status=status.HTTP_201_CREATED,
        )


class DirectorTeacherDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Teacher.objects.filter(
            centers__in=centers, user__is_deleted=False
        ).select_related("user", "centers")

    def get_serializer_class(self):
        return (
            DirectorTeacherCreateSerializer
            if self.request.method == "PATCH"
            else DirectorTeacherDetailSerializer
        )

    @extend_schema(tags=["3. Director — Teachers"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["3. Director — Teachers"])
    def patch(self, request, *args, **kwargs):
        center = get_director_centers(request.user).first()
        instance = self.get_object()
        serializer = DirectorTeacherCreateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request, "center": center},
        )
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(DirectorTeacherDetailSerializer(teacher).data)

    @extend_schema(tags=["3. Director — Teachers"])
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class DirectorRoomListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorRoomSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return Room.objects.all().order_by("name")

    @extend_schema(tags=["4. Director — Rooms"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["4. Director — Rooms"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DirectorRoomDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorRoomSerializer
    http_method_names = ["get", "patch", "delete"]
    queryset = Room.objects.all()

    @extend_schema(tags=["4. Director — Rooms"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["4. Director — Rooms"])
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["4. Director — Rooms"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class DirectorCourseListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorCourseSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["name"]
    ordering_fields = ["name", "price", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Course.objects.filter(center__in=centers)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = get_director_centers(self.request.user).first()
        return ctx

    @extend_schema(tags=["5. Director — Courses"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["5. Director — Courses"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DirectorCourseDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorCourseSerializer
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Course.objects.filter(center__in=centers)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = get_director_centers(self.request.user).first()
        return ctx

    @extend_schema(tags=["5. Director — Courses"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["5. Director — Courses"])
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=["5. Director — Courses"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ─── Groups ──────────────────────────────────────────────────────────────────


class DirectorGroupListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "course", "teacher"]
    search_fields = ["name", "course__name", "teacher__user__first_name"]
    ordering_fields = ["created_at", "start_date", "student_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Group.objects.filter(center__in=centers).select_related(
            "course", "teacher__user", "room"
        )

    def get_serializer_class(self):
        return (
            DirectorGroupCreateSerializer
            if self.request.method == "POST"
            else DirectorGroupListSerializer
        )

    def _get_center(self):
        return get_director_centers(self.request.user).first()

    @extend_schema(tags=["6. Director — Groups"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["6. Director — Groups"])
    def post(self, request, *args, **kwargs):
        center = self._get_center()
        serializer = DirectorGroupCreateSerializer(
            data=request.data,
            context={"request": request, "center": center},
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(
            DirectorGroupDetailSerializer(group).data, status=status.HTTP_201_CREATED
        )


class DirectorGroupDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return (
            Group.objects.filter(center__in=centers)
            .select_related("course", "teacher__user", "room")
            .prefetch_related("enrollments__student__user")
        )

    def get_serializer_class(self):
        return (
            DirectorGroupCreateSerializer
            if self.request.method == "PATCH"
            else DirectorGroupDetailSerializer
        )

    def _get_center(self):
        return get_director_centers(self.request.user).first()

    @extend_schema(tags=["6. Director — Groups"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["6. Director — Groups"])
    def patch(self, request, *args, **kwargs):
        center = self._get_center()
        instance = self.get_object()
        serializer = DirectorGroupCreateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request, "center": center},
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(DirectorGroupDetailSerializer(group).data)

    @extend_schema(tags=["6. Director — Groups"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class DirectorGroupEnrollView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def _get_group(self, pk):
        centers = get_director_centers(self.request.user)
        try:
            return Group.objects.get(pk=pk, center__in=centers)
        except Group.DoesNotExist:
            raise NotFound("Guruh topilmadi.")

    @extend_schema(tags=["6. Director — Groups"])
    def post(self, request, pk):
        group = self._get_group(pk)
        center = get_director_centers(request.user).first()
        serializer = DirectorGroupEnrollSerializer(
            data=request.data,
            context={"request": request, "center": center, "group": group},
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(DirectorGroupDetailSerializer(group).data)


class DirectorLessonListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["group"]
    ordering_fields = ["date", "start_time"]
    ordering = ["-date"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Lesson.objects.filter(group__center__in=centers).select_related("group")

    def get_serializer_class(self):
        return (
            DirectorLessonCreateSerializer
            if self.request.method == "POST"
            else DirectorLessonListSerializer
        )

    def _get_center(self):
        return get_director_centers(self.request.user).first()

    @extend_schema(tags=["7. Director — Lessons"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["7. Director — Lessons"])
    def post(self, request, *args, **kwargs):
        center = self._get_center()
        serializer = DirectorLessonCreateSerializer(
            data=request.data,
            context={"request": request, "center": center},
        )
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        return Response(
            DirectorLessonListSerializer(lesson).data, status=status.HTTP_201_CREATED
        )


class DirectorLessonDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        centers = get_director_centers(self.request.user)
        return Lesson.objects.filter(group__center__in=centers).select_related("group")

    def get_serializer_class(self):
        return (
            DirectorLessonCreateSerializer
            if self.request.method == "PATCH"
            else DirectorLessonListSerializer
        )

    def _get_center(self):
        return get_director_centers(self.request.user).first()

    @extend_schema(tags=["7. Director — Lessons"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["7. Director — Lessons"])
    def patch(self, request, *args, **kwargs):
        center = self._get_center()
        instance = self.get_object()
        serializer = DirectorLessonCreateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request, "center": center},
        )
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        return Response(DirectorLessonListSerializer(lesson).data)

    @extend_schema(tags=["7. Director — Lessons"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class DirectorAttendanceView(APIView):
    def _get_lesson(self, pk):
        centers = get_director_centers(self.request.user)
        try:
            return Lesson.objects.get(pk=pk, group__center__in=centers)
        except Lesson.DoesNotExist:
            raise NotFound("Dars topilmadi.")

    @extend_schema(tags=["8. Director — Attendance"])
    def get(self, request, pk):
        lesson = self._get_lesson(pk)
        attendances = Attendance.objects.filter(lesson=lesson).select_related(
            "student__user"
        )
        serializer = DirectorAttendanceSerializer(attendances, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["8. Director — Attendance"])
    def post(self, request, pk):
        lesson = self._get_lesson(pk)
        serializer = DirectorAttendanceBulkSerializer(
            data=request.data,
            context={"request": request, "lesson": lesson},
        )
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        return Response(DirectorAttendanceSerializer(results, many=True).data)
