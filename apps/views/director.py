from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from apps.models import Center, Student, Teacher, Group, Room, Course, Lesson, Attendance
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
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.permissions import IsDirector
from service import get_dashboard_data, get_director_centers, get_single_center_or_404


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
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
    filter_backends = [filters.SearchFilter]
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


@extend_schema(tags=["DirectorGroup"])
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
        if self.request.method == "POST":
            return DirectorGroupCreateSerializer
        else:
            return DirectorGroupListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context


@extend_schema(tags=["DirectorGroup"])
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
        return Response(DirectorGroupListSerializer(group).data)


@extend_schema(tags=["DirectorLesson"])
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
