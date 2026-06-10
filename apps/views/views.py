from django.http import Http404
from django.utils.functional import cached_property
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.models import User, Group, Room, GroupStudent
from apps.serializers import StudentProfileSerializer, AdminProfileSerializer, \
    GroupModelSerializer, RoomModelSerializer, GroupStudentModelSerializer
from apps.serializers.profile_serializers import TeacherProfileSerializer, ParentProfileSerializer


@extend_schema(tags=['Profile'])
class MyProfileRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']

    @cached_property
    def _user_with_profiles(self):
        return (
            User.objects
            .select_related(
                'student_profile',
                'teacher_profile',
                'parent_profile',
            )
            .get(pk=self.request.user.pk)
        )

    def get_serializer_class(self):
        role = self._user_with_profiles.role

        role_serializer_map = {
            User.Role.STUDENT: StudentProfileSerializer,
            User.Role.TEACHER: TeacherProfileSerializer,
            User.Role.PARENT:  ParentProfileSerializer,
        }

        return role_serializer_map.get(role, AdminProfileSerializer)

    def get_object(self):
        user = self._user_with_profiles

        role_profile_map = {
            User.Role.STUDENT: ('student_profile', "Talaba profili bazadan topilmadi."),
            User.Role.TEACHER: ('teacher_profile', "O'qituvchi profili bazadan topilmadi."),
            User.Role.PARENT:  ('parent_profile',  "Ota-ona profili bazadan topilmadi."),
        }

        if user.role in role_profile_map:
            attr, msg = role_profile_map[user.role]
            profile = getattr(user, attr, None)
            if profile is None:
                raise Http404(msg)
            return profile

        return user


@extend_schema(tags=['Group'])
class GroupModelViewSet(ModelViewSet):
    queryset = Group.objects.select_related('room', 'teacher__user')
    permission_classes = [AllowAny]
    serializer_class = GroupModelSerializer
    http_method_names = ['get', 'post', 'patch']


@extend_schema(tags=['Group_Students'])
class GroupStudentModelViewSet(ModelViewSet):
    queryset = GroupStudent.objects.select_related('group__room')
    permission_classes = [AllowAny]
    serializer_class = GroupStudentModelSerializer
    http_method_names = ['get', 'post', 'patch']


@extend_schema(tags=['Room'])
class RoomModelViewSet(ModelViewSet):
    queryset = Room.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RoomModelSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
