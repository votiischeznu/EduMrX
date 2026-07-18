from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.constants import DAY_NAMES

from apps.models import Attendance
from apps.permissions import IsManagerOrDirectorOrSuperAdmin
from apps.service import get_director_centers
from apps.views.manager import get_manager_branch_or_404


@extend_schema(tags=["Attendance"])
class AttendanceOverviewAPIView(APIView):
    # FIX: avval [IsAuthenticated] edi — har qanday rol (student/parent/
    # teacher ham) kira olardi va queryset markaz/filial bo'yicha
    # cheklanmagan edi, ya'ni har kim BUTUN platforma davomatini ko'rar
    # edi. Endi faqat Manager/Direktor/Super Admin kira oladi, va har
    # birining ko'rgan ma'lumoti o'ziga tegishli markaz/filial bilan
    # cheklanadi.
    permission_classes = [IsManagerOrDirectorOrSuperAdmin]

    def _get_scoped_queryset(self, user, start_date, end_date):
        qs = Attendance.objects.filter(lesson__date__range=[start_date, end_date])

        if user.is_super_admin:
            return qs

        if user.is_director:
            centers = get_director_centers(user)
            return qs.filter(lesson__group__center__in=centers)

        if user.is_admin:
            center, branch = get_manager_branch_or_404(user)
            return qs.filter(lesson__group__center=center, lesson__group__branch=branch)

        # IsManagerOrDirectorOrSuperAdmin buni normal holatda o'tkazmasligi
        # kerak, lekin ehtiyot uchun bo'sh queryset qaytariladi.
        return Attendance.objects.none()

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
            self._get_scoped_queryset(request.user, start_date, end_date)
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