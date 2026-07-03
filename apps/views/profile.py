from django.http import Http404
from django.utils.functional import cached_property
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.models import Group, GroupStudent, Room, User
from apps.serializers import (
    AdminProfileSerializer,
    DirectorProfileSerializer,
    GroupModelSerializer,
    GroupStudentModelSerializer,
    ParentProfileSerializer,
    RoomModelSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
)

@extend_schema(tags=["Profile"])
class MyProfileRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    @cached_property
    def _user_with_profiles(self):
        # Profil modellari mavjud bo'lgan barcha related_name larni select_related ga qo'shdik
        return (
            User.objects.select_related(
                "student_profile",
                "teacher_profile",
                "parent_profile",
                # Agar Manager uchun alohida model ishlatayotgan bo'lsangiz, uni ham qo'shing:
                # "staff_profile",
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

        # Agar rolda profil bo'lmasa, userning o'zini qaytaradi
        return user


@extend_schema(tags=["Groups"])
class GroupModelViewSet(ModelViewSet):
    queryset = Group.objects.select_related("room", "teacher__user")
    permission_classes = [AllowAny]
    serializer_class = GroupModelSerializer
    http_method_names = ["get", "post", "patch"]


@extend_schema(tags=["Group_Students"])
class GroupStudentModelViewSet(ModelViewSet):
    queryset = GroupStudent.objects.select_related("group__room")
    permission_classes = [AllowAny]
    serializer_class = GroupStudentModelSerializer
    http_method_names = ["get", "post", "patch"]


@extend_schema(tags=["Rooms"])
class RoomModelViewSet(ModelViewSet):
    queryset = Room.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RoomModelSerializer
    http_method_names = ["get", "post", "patch", "delete"]
