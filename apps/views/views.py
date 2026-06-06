from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
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

    def get_serializer_class(self):
        role = self.request.user.role

        if role == User.Role.STUDENT:
            return StudentProfileSerializer
        elif role == User.Role.TEACHER:
            return TeacherProfileSerializer
        elif role == User.Role.PARENT:
            return ParentProfileSerializer

        return AdminProfileSerializer

    def get_object(self):
        user = self.request.user
        try:
            if user.role == User.Role.STUDENT:
                if not hasattr(user, 'student_profile'):
                    raise Http404("Talaba profili bazadan topilmadi.")
                return user.student_profile
            elif user.role == User.Role.TEACHER:
                if not hasattr(user, 'teacher_profile'):
                    raise Http404("O'qituvchi profili bazadan topilmadi.")
                return user.teacher_profile
            elif user.role == User.Role.PARENT:
                if not hasattr(user, 'parent_profile'):
                    raise Http404("Ota-ona profili bazadan topilmadi.")
                return user.parent_profile
        except ObjectDoesNotExist:
            raise Http404("Profil topilmadi.")

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
