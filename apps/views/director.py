from datetime import date

from django.db.models import DecimalField, Q
from django.db.models.aggregates import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from apps.models import Center, Student, Teacher, Group, Room, Course, Lesson, Attendance, Payment, Debt
from apps.serializers import (
    DirectorTeacherCreateSerializer,
    DirectorTeacherListSerializer,
    DirectorRoomSerializer,
    DirectorCourseSerializer,
    DirectorGroupCreateSerializer,
    DirectorGroupEnrollSerializer,
    DirectorGroupListSerializer,
    DirectorLessonCreateSerializer,
    DirectorLessonListSerializer,
    DirectorAttendanceBulkSerializer,
    DirectorAttendanceSerializer,
    DirectorStudentCreateSerializer,
    DirectorStudentListSerializer,
)

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.permissions import IsDirector


def get_director_centers(user):
    return Center.objects.filter(director=user)


def get_single_center_or_404(user):
    center = get_director_centers(user).first()
    if not center:
        raise NotFound("Sizga biriktirilgan markaz topilmadi.")
    return center


@extend_schema(tags=["1. Director"])
class DirectorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def get(self, request):
        user = request.user
        center = Center.objects.filter(director=user).first()
        if not center:
            return Response({"detail": "Sizga biriktirilgan markaz topilmadi."}, status=404)

        today = date.today()
        current_year = today.year
        current_month = today.month

        total_students = center.students.filter(user__is_deleted=False).count()
        active_students = center.students.filter(
            status=Student.Status.ACTIVE,
            user__is_deleted=False,
        ).count()
        total_teachers = center.teachers.filter(user__is_deleted=False).count()
        total_groups = center.groups.count()
        active_groups = center.groups.filter(status=Group.Status.ACTIVE).count()

        monthly_revenue = Payment.objects.filter(
            student__center=center,
            status=Payment.Status.PAID,
            period_year=current_year,
            period_month=current_month,
        ).aggregate(total=Sum("final_amount", default=0))["total"]

        total_debt = Debt.objects.filter(
            student__center=center,
            status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID],
        ).aggregate(total=Sum("amount", default=0))["total"]

        revenue_chart = (
            Payment.objects.filter(student__center=center, status=Payment.Status.PAID)
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

        group_stats = center.groups.values("status").annotate(count=Count("id"))
        group_distribution = {g["status"]: g["count"] for g in group_stats}

        top_groups = (
            Group.objects.filter(center=center)
            .annotate(
                revenue=Sum(
                    "payments__final_amount",
                    filter=Q(payments__status=Payment.Status.PAID),
                    default=0,
                )
            )
            .order_by("-revenue")[:5]
            .values("id", "name", "student_count", "status", "revenue")
        )

        recent_payments = (
            Payment.objects.filter(student__center=center, status=Payment.Status.PAID)
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


@extend_schema_view(
    get=extend_schema(tags=["2. Director — Students"]),
    post=extend_schema(tags=["2. Director — Students"]),
)
class DirectorStudentListCreateView(ListCreateAPIView):
    queryset = Student.objects.filter(user__is_deleted=False).select_related("user", "center", "parent__user")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["enrolled_at", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)

    def get_serializer_class(self):
        return DirectorStudentCreateSerializer if self.request.method == "POST" else DirectorStudentListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["centers"] = get_director_centers(self.request.user)
        return context


@extend_schema_view(
    get=extend_schema(tags=["2. Director — Students"]),
    patch=extend_schema(tags=["2. Director — Students"]),
    delete=extend_schema(tags=["2. Director — Students"]),
)
class DirectorStudentDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.select_related("user", "center", "parent__user")
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        return DirectorStudentCreateSerializer if self.request.method == "PATCH" else DirectorStudentListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["centers"] = get_director_centers(self.request.user)
        return context

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(tags=["3. Director — Teachers"]),
    post=extend_schema(tags=["3. Director — Teachers"]),
)
class DirectorTeacherListCreateView(ListCreateAPIView):
    queryset = Teacher.objects.select_related("user", "centers")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["created_at", "experience"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(centers__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        return DirectorTeacherCreateSerializer if self.request.method == "POST" else DirectorTeacherListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema_view(
    get=extend_schema(tags=["3. Director — Teachers"]),
    patch=extend_schema(tags=["3. Director — Teachers"]),
    delete=extend_schema(tags=["3. Director — Teachers"]),
)
class DirectorTeacherDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Teacher.objects.select_related("user", "centers")
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(centers__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        return DirectorTeacherCreateSerializer if self.request.method == "PATCH" else DirectorTeacherListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.user.is_deleted = True
        instance.user.is_active = False
        instance.user.save(update_fields=["is_deleted", "is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(tags=["4. Director — Rooms"]),
    post=extend_schema(tags=["4. Director — Rooms"]),
)
class DirectorRoomListCreateView(ListCreateAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorRoomSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers).order_by("name")

    def perform_create(self, serializer):
        center = get_single_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema_view(
    get=extend_schema(tags=["4. Director — Rooms"]),
    patch=extend_schema(tags=["4. Director — Rooms"]),
    delete=extend_schema(tags=["4. Director — Rooms"]),
)
class DirectorRoomDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorRoomSerializer
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)


@extend_schema_view(
    get=extend_schema(tags=["5. Director — Courses"]),
    post=extend_schema(tags=["5. Director — Courses"]),
)
class DirectorCourseListCreateView(ListCreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorCourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["name"]
    ordering_fields = ["name", "price", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)

    def perform_create(self, serializer):
        center = get_single_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema_view(
    get=extend_schema(tags=["5. Director — Courses"]),
    patch=extend_schema(tags=["5. Director — Courses"]),
    delete=extend_schema(tags=["5. Director — Courses"]),
)
class DirectorCourseDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorCourseSerializer
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)


# ──────────────────────────────────────────────────────────────────────────
# GROUP
# ──────────────────────────────────────────────────────────────────────────


@extend_schema_view(
    get=extend_schema(tags=["6. Director — Groups"]),
    post=extend_schema(tags=["6. Director — Groups"]),
)
class DirectorGroupListCreateView(ListCreateAPIView):
    queryset = Group.objects.select_related("course", "teacher__user", "room")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "course", "teacher"]
    search_fields = ["name", "course__name", "teacher__user__first_name"]
    ordering_fields = ["created_at", "start_date", "student_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)

    def get_serializer_class(self):
        return DirectorGroupCreateSerializer if self.request.method == "POST" else DirectorGroupListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema_view(
    get=extend_schema(tags=["6. Director — Groups"]),
    patch=extend_schema(tags=["6. Director — Groups"]),
    delete=extend_schema(tags=["6. Director — Groups"]),
)
class DirectorGroupDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.select_related("course", "teacher__user", "room").prefetch_related(
        "enrollments__student__user"
    )
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)

    def get_serializer_class(self):
        return DirectorGroupCreateSerializer if self.request.method == "PATCH" else DirectorGroupListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema(tags=["6. Director — Groups"])
class DirectorGroupEnrollView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorGroupEnrollSerializer

    def get_serializer_context(self):
        group = self._get_group(self.kwargs["pk"])
        return {
            "request": self.request,
            "center": group.center,
            "group": group,
        }

    def _get_group(self, pk):
        centers = get_director_centers(self.request.user)
        try:
            return Group.objects.get(pk=pk, center__in=centers)
        except Group.DoesNotExist:
            raise NotFound("Guruh topilmadi.")

    def post(self, request, pk):
        serializer = self.serializer_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(DirectorGroupListSerializer(group).data)


# ──────────────────────────────────────────────────────────────────────────
# LESSON
# ──────────────────────────────────────────────────────────────────────────


@extend_schema_view(
    get=extend_schema(tags=["7. Director — Lessons"]),
    post=extend_schema(tags=["7. Director — Lessons"]),
)
class DirectorLessonListCreateView(ListCreateAPIView):
    queryset = Lesson.objects.select_related("group")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["group"]
    ordering_fields = ["date", "start_time"]
    ordering = ["-date"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(group__center__in=centers)

    def get_serializer_class(self):
        return DirectorLessonCreateSerializer if self.request.method == "POST" else DirectorLessonListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema_view(
    get=extend_schema(tags=["7. Director — Lessons"]),
    patch=extend_schema(tags=["7. Director — Lessons"]),
    delete=extend_schema(tags=["7. Director — Lessons"]),
)
class DirectorLessonDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related("group")
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(group__center__in=centers)

    def get_serializer_class(self):
        return DirectorLessonCreateSerializer if self.request.method == "PATCH" else DirectorLessonListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


# ──────────────────────────────────────────────────────────────────────────
# ATTENDANCE
# ──────────────────────────────────────────────────────────────────────────


@extend_schema(tags=["8. Director — Attendance"])
class DirectorAttendanceView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def _get_lesson(self, pk):
        centers = get_director_centers(self.request.user)
        try:
            return Lesson.objects.get(pk=pk, group__center__in=centers)
        except Lesson.DoesNotExist:
            raise NotFound("Dars topilmadi.")

    def get(self, request, pk):
        lesson = self._get_lesson(pk)
        attendances = Attendance.objects.filter(lesson=lesson).select_related("student__user")
        serializer = DirectorAttendanceSerializer(attendances, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        lesson = self._get_lesson(pk)
        serializer = DirectorAttendanceBulkSerializer(
            data=request.data,
            context={"request": request, "lesson": lesson},
        )
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        return Response(DirectorAttendanceSerializer(results, many=True).data)
