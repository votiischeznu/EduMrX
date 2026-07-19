from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Attendance
from apps.permissions import IsStudent
from apps.serializers import (
    StudentAttendanceSerializer,
    StudentDashboardSerializer,
)


@extend_schema(tags=["StudentDashboard"])
class StudentDashboardView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        student = getattr(request.user, "student_profile", None)
        if student is None:
            return Response({"detail": "Talaba profili topilmadi."}, status=404)
        return Response(StudentDashboardSerializer(student).data)


@extend_schema(tags=["StudentAttendance"])
class StudentAttendanceListView(ListAPIView):
    permission_classes = [IsStudent]
    serializer_class = StudentAttendanceSerializer

    def get_queryset(self):
        student = getattr(self.request.user, "student_profile", None)
        if student is None:
            return Attendance.objects.none()

        qs = Attendance.objects.filter(student=student).select_related("lesson", "lesson__group")

        group_id = self.request.query_params.get("group")
        if group_id:
            qs = qs.filter(lesson__group_id=group_id)

        return qs.order_by("-lesson__date")
