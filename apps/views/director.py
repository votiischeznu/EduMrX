from datetime import date

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.exceptions import NotFound


from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.permissions import IsDirector

from apps.models import Center, Student, Teacher, Group, Room, Course, Lesson, Attendance, CenterStaff, Branch
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
    DirectorAdminCreateSerializer,
    DirectorAdminDetailSerializer,
    DirectorAdminListSerializer,
)
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from apps.service.director_dashboard import get_dashboard_data, get_director_centers, get_single_center_or_404
from apps.service.director_finance_service import (
    DirectorFinanceService,
    DirectorFinanceChartService,
    DirectorFinanceTransactionsService,
    DirectorFinanceBranchesService,
)


class DirectorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def get(self, request):
        center = Center.objects.filter(director=request.user).first()
        if not center:
            return Response({"detail": "Sizga biriktirilgan markaz topilmadi."}, status=404)
        data = get_dashboard_data(center)
        return Response(data)


@extend_schema(tags=["DirectorStudents"])
class DirectorStudentListCreateView(ListCreateAPIView):
    queryset = Student.objects.filter(user__is_deleted=False).select_related("user", "center", "parent__user")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["enrolled_at", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorStudentCreateSerializer
        else:
            return DirectorStudentListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["centers"] = get_director_centers(self.request.user)
        return context


@extend_schema(tags=["2. DirectorStudents"])
class DirectorStudentDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.select_related("user", "center", "parent__user")
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DirectorStudentCreateSerializer
        else:
            return DirectorStudentListSerializer

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


@extend_schema(tags=["DirectorTeacher"])
class DirectorTeacherListCreateView(ListCreateAPIView):
    queryset = Teacher.objects.prefetch_related("user", "centers")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["created_at", "experience"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(centers__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorTeacherCreateSerializer
        else:
            return DirectorTeacherListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema(tags=["DirectorTeacher"])
class DirectorTeacherDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Teacher.objects.prefetch_related("user", "centers")
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(centers__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DirectorTeacherCreateSerializer
        else:
            return DirectorTeacherListSerializer

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


@extend_schema(tags=["DirectorRoom"])
class DirectorRoomListCreateView(ListCreateAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorRoomSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers).order_by("name")

    def perform_create(self, serializer):
        center = get_single_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["DirectorRoom"])
class DirectorRoomDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorRoomSerializer
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)


@extend_schema(tags=["DirectorCourse"])
class DirectorCourseListCreateView(ListCreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorCourseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["name"]
    ordering_fields = ["name", "price", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(center__in=get_director_centers(self.request.user))

    def perform_create(self, serializer):
        center = get_single_center_or_404(self.request.user)
        serializer.save(center=center)


@extend_schema(tags=["DirectorCourse"])
class DirectorCourseDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = DirectorCourseSerializer
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)


@extend_schema(tags=["DirectorGroups"])
class DirectorGroupListCreateView(ListCreateAPIView):
    queryset = Group.objects.select_related("course", "teacher__user", "room")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "course", "teacher"]
    search_fields = ["name", "course__name", "teacher__user__first_name"]
    ordering_fields = ["created_at", "start_date", "student_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorGroupCreateSerializer
        else:
            return DirectorGroupListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema(tags=["DirectorGroups"])
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
        if self.request.method == "PATCH":
            return DirectorGroupCreateSerializer
        else:
            return DirectorGroupListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema(tags=["DirectorGroups"])
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
        return Response(DirectorGroupListSerializer(group, context=self.get_serializer_context()).data)


@extend_schema(tags=["DirectorLesson"])
class DirectorLessonListCreateView(ListCreateAPIView):
    queryset = Lesson.objects.select_related("group")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["group"]
    ordering_fields = ["date", "start_time"]
    ordering = ["-date"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(group__center__in=centers)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorLessonCreateSerializer
        else:
            return DirectorLessonListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema(tags=["DirectorLesson"])
class DirectorLessonDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related("group")
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(group__center__in=centers)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DirectorLessonCreateSerializer
        else:
            return DirectorLessonListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema(tags=["DirectorAttendance"])
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


@extend_schema(tags=["DirectorAdmin"])
class DirectorAdminListCreateView(ListCreateAPIView):
    queryset = CenterStaff.objects.select_related("user", "center")
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["center"]
    search_fields = ["user__first_name", "user__last_name", "user__phone"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DirectorAdminCreateSerializer
        return DirectorAdminListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["centers"] = get_director_centers(self.request.user)
        return context


@extend_schema(tags=["DirectorAdmin"])
class DirectorAdminDetailView(RetrieveUpdateDestroyAPIView):
    queryset = CenterStaff.objects.select_related("user", "center")
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = super().get_queryset()
        centers = get_director_centers(self.request.user)
        return qs.filter(center__in=centers, user__is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DirectorAdminCreateSerializer
        return DirectorAdminDetailSerializer

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



class DirectorAnalyticsBaseView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def get_centers_and_branch(self, request):
        centers = get_director_centers(request.user)
        branch = None
        branch_id = request.query_params.get("branch_id")
        if branch_id:
            try:
                branch = Branch.objects.get(id=branch_id, center__in=centers)
            except Branch.DoesNotExist:
                raise NotFound("Filial topilmadi yoki sizga tegishli emas.")
        return centers, branch


@extend_schema(tags=["DirectorAnalytics"])
class DirectorAnalyticsBranchTabsView(DirectorAnalyticsBaseView):
    """
    GET /api/v1/director/analytics/branches/
    'Filial tahlili' sahifasidagi tab/tugmalar uchun yengil ro'yxat
    (id + name, hech qanday moliyaviy hisob-kitobsiz).
    """

    def get(self, request):
        centers, _ = self.get_centers_and_branch(request)
        branches = Branch.objects.filter(center__in=centers).values("id", "name", "status")
        data = [{"id": str(b["id"]), "name": b["name"], "status": b["status"]} for b in branches]
        return Response({"status": "success", "data": data})


@extend_schema(tags=["DirectorAnalytics"])
class DirectorAnalyticsSummaryView(DirectorAnalyticsBaseView):
    """GET /api/v1/director/analytics/summary/?branch_id=<uuid> (ixtiyoriy)"""

    def get(self, request):
        centers, branch = self.get_centers_and_branch(request)
        data = DirectorFinanceService.get_summary_data(centers, branch=branch)
        return Response({"status": "success", "data": data})


@extend_schema(tags=["DirectorAnalytics"])
class DirectorAnalyticsChartView(DirectorAnalyticsBaseView):
    """GET /api/v1/director/analytics/chart/?year=2026&branch_id=<uuid>"""

    def get(self, request):
        centers, branch = self.get_centers_and_branch(request)
        year = int(request.query_params.get("year", date.today().year))
        data = DirectorFinanceChartService.get_top_branches_yearly_chart(centers, year, branch=branch)
        return Response({"status": "success", "data": data})


@extend_schema(tags=["DirectorAnalytics"])
class DirectorAnalyticsTransactionsView(DirectorAnalyticsBaseView):
    """GET /api/v1/director/analytics/transactions/?page=1&limit=10&branch_id=<uuid>"""

    def get(self, request):
        centers, branch = self.get_centers_and_branch(request)
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("limit", 10))
        data, total = DirectorFinanceTransactionsService.get_transactions_list_with_student(
            centers, page, per_page, branch=branch
        )
        return Response({"status": "success", "data": data})


@extend_schema(tags=["DirectorAnalytics"])
class DirectorAnalyticsBranchesView(DirectorAnalyticsBaseView):
    """
    GET /api/v1/director/analytics/centers/?page=1&limit=5&status=all&search=...&sort_by=...&sort_dir=...
    Eslatma: nom 'centers' bo'lib qoladi (SuperAdmin bilan bir xil URL shakli uchun),
    lekin Director uchun mazmunan bu o'z markazidagi FILIALLAR jadvali.
    """

    def get(self, request):
        centers, _branch = self.get_centers_and_branch(request)
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("limit", 5))
        status_filter = request.query_params.get("status", "all")
        search = request.query_params.get("search", "")
        sort_by = request.query_params.get("sort_by", "month_revenue")
        sort_dir = request.query_params.get("sort_dir", "desc")

        data, total = DirectorFinanceBranchesService.get_branches_finance_list(
            centers, status_filter, search, sort_by, sort_dir, page, per_page
        )
        return Response(
            {
                "status": "success",
                "data": data,
                "meta": {"current_page": page, "per_page": per_page, "total": total},
            }
        )
