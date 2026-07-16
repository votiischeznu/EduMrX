from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.models import Attendance, Group, Lesson
from apps.permissions import IsTeacher
from apps.serializers import (
    AttendanceMarkSerializer,
    AttendanceSerializer,
    TeacherGroupSerializer,
    TeacherLessonSerializer,
    TeacherSalarySerializer
)


class TeacherGroupViewSet(ReadOnlyModelViewSet):
    """Teacherga biriktirilgan guruhlar: xona, faol o'quvchilar, hafta kunlari.

    Teacher bitta center/branchga biriktirilgani uchun (Teacher.centers,
    Teacher.branch) qo'shimcha query param shart emas.
    """

    serializer_class = TeacherGroupSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        teacher = self.request.user.teacher_profile
        qs = Group.objects.filter(teacher=teacher, center=teacher.centers)
        if teacher.branch_id:
            qs = qs.filter(branch=teacher.branch)

        return (
            qs.select_related("room")
            .prefetch_related("enrollments__student__user")
            .annotate(active_student_count=Count("enrollments", filter=Q(enrollments__is_active=True), distinct=True))
        )


class TeacherSalaryView(APIView):
    """Teacherning maoshi — hozircha faqat statik summa (Teacher.salary).

    To'lov sanasi/tarixi uchun modelda maydon yo'q.
    """

    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        teacher = request.user.teacher_profile
        serializer = TeacherSalarySerializer(teacher)
        return Response(serializer.data)


class TeacherLessonViewSet(ModelViewSet):
    """Teacher o'z guruhlarining darslarini ko'radi, mavzu kiritadi/tahrirlaydi,
    va shu dars uchun davomat belgilaydi.
    """

    serializer_class = TeacherLessonSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        teacher = self.request.user.teacher_profile
        return Lesson.objects.filter(group__teacher=teacher, group__center=teacher.centers).select_related(
            "group", "group__course", "group__room"
        )

    @action(detail=False, methods=["post"], url_path="groups/(?P<group_id>[^/.]+)/today")
    def today(self, request, group_id=None):
        """Bugungi darsni qaytaradi — mavjud bo'lmasa yaratadi.

        Manager oldindan mavzu kiritgan bo'lsa `topic` to'ldirilgan holda
        keladi; bo'sh bo'lsa teacher PATCH orqali o'zi kiritadi.
        """
        teacher = request.user.teacher_profile
        group = get_object_or_404(Group, id=group_id, teacher=teacher, center=teacher.centers)
        lesson, _ = Lesson.objects.get_or_create(
            group=group,
            date=timezone.now().date(),
            defaults={
                "start_time": group.lesson_start_time,
                "end_time": group.lesson_end_time,
            },
        )
        serializer = self.get_serializer(lesson)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="attendance")
    def mark_attendance(self, request, pk=None):
        """Payload: [{"student": "<uuid>", "status": "present", "note": ""}, ...]"""
        lesson = self.get_object()
        serializer = AttendanceMarkSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        active_student_ids = set(lesson.group.enrollments.filter(is_active=True).values_list("student_id", flat=True))

        results = []
        for item in serializer.validated_data:
            if item["student"] not in active_student_ids:
                continue
            attendance, _ = Attendance.objects.update_or_create(
                lesson=lesson,
                student_id=item["student"],
                defaults={
                    "status": item["status"],
                    "note": item.get("note", ""),
                },
            )
            results.append(attendance)

        return Response(AttendanceSerializer(results, many=True).data, status=status.HTTP_200_OK)
