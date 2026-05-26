from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ModelViewSet

from apps.models import User, Group, Room, GroupStudent
from apps.serializers import StudentProfileSerializer, TeacherProfileSerializer, AdminProfileSerializer, \
    GroupModelSerializer, RoomModelSerializer, GroupStudentModelSerializer


@extend_schema(tags=['Profile'])
class MyProfileRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', ]

    def get_serializer_class(self):
        role = self.request.user.role

        if role == User.Role.STUDENT:
            return StudentProfileSerializer

        elif role == User.Role.TEACHER:
            return TeacherProfileSerializer

        return AdminProfileSerializer

    def get_object(self):
        return self.request.user


@extend_schema(tags=['Room'])
class GroupModelViewSet(ModelViewSet):
    queryset = Group.objects.all()
    permission_classes = [AllowAny]
    serializer_class = GroupModelSerializer
    http_method_names = ['get', 'post', 'patch']



@extend_schema(tags=['Group'])
class RoomModelViewSet(ModelViewSet):
    queryset = Room.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RoomModelSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']


@extend_schema(tags=['Group_Students'])
class GroupStudentModelViewSet(ModelViewSet):
    queryset = GroupStudent.objects.all()
    permission_classes = [AllowAny]
    serializer_class = GroupStudentModelSerializer
    http_method_names = ['get', 'post', 'patch']
