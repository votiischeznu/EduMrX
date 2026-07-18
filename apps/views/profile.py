from django.http import Http404
from django.utils.functional import cached_property
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.models import User
from apps.serializers import (
    AdminProfileSerializer,
    DirectorProfileSerializer,
    ParentProfileSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
)


@extend_schema(tags=["Profile"])
class MyProfileRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    @cached_property
    def _user_with_profiles(self):
        return (
            User.objects.select_related(
                "student_profile",
                "teacher_profile",
                "parent_profile",
            )
            .prefetch_related("directed_centers", "centers")
            .get(pk=self.request.user.pk)
        )

    def get_serializer_class(self):
        role_serializer_map = {
            User.Role.STUDENT: StudentProfileSerializer,
            User.Role.TEACHER: TeacherProfileSerializer,
            User.Role.PARENT: ParentProfileSerializer,
            User.Role.DIRECTOR: DirectorProfileSerializer,
            User.Role.ADMIN: AdminProfileSerializer,
        }
        return role_serializer_map.get(self.request.user.role, AdminProfileSerializer)

    def get_object(self):
        user = self._user_with_profiles

        if user.is_staff or user.is_director or user.is_super_admin:
            return user

        role_profile_map = {
            User.Role.STUDENT: ("student_profile", "Talaba profili topilmadi."),
            User.Role.TEACHER: ("teacher_profile", "O'qituvchi profili topilmadi."),
            User.Role.PARENT: ("parent_profile", "Ota-ona profili topilmadi."),
        }

        attr, msg = role_profile_map.get(user.role, (None, None))

        if attr:
            profile = getattr(user, attr, None)
            if profile is None:
                raise Http404(msg)
            return profile

        return user
