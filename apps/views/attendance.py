from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.constants import DAY_NAMES

from apps.models import Attendance


@extend_schema(tags=["Attendance"])
class AttendanceOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "this_week")
        today = timezone.now().date()

        # 1. Establish clear date boundaries
        if period == "this_week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == "last_week":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = start_date + timedelta(days=6)
        elif period == "this_month":
            start_date = today.replace(day=1)
            next_month = (start_date + timedelta(days=32)).replace(day=1)
            end_date = next_month - timedelta(days=1)
        else:
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

        attendance_data = (
            Attendance.objects.filter(lesson__date__range=[start_date, end_date])
            .values("lesson__date")
            .annotate(
                present_count=Count("pk", filter=Q(status=Attendance.Status.PRESENT)),
                absent_count=Count("pk", filter=Q(status=Attendance.Status.ABSENT)),
            )
        )

        attendance_map = {}
        for item in attendance_data:
            date_key = item["lesson__date"]
            if date_key:
                attendance_map[date_key] = (item["present_count"], item["absent_count"])

        # 2. DAY_NAMES lug'atini bu yerdan olib tashlang!

        result = []
        current = start_date

        while current <= end_date:
            present, absent = attendance_map.get(current, (0, 0))

            result.append(
                {
                    "day": DAY_NAMES.get(current.weekday(), "Noma'lum"),
                    "date": str(current),
                    "present": present,
                    "absent": absent,
                }
            )
            current += timedelta(days=1)

        return Response(result)
