from apps.serializers.auth_serializer import LoginModelSerializer, RegisterModelSerializer
from apps.serializers.auth_serializer import (
    RegisterModelSerializer,
    LoginModelSerializer,
    RecoveryStartSerializer,
    RecoveryVerifySerializer,
    RecoveryCompleteSerializer
)
from apps.serializers.group_serializer import GroupModelSerializer, RoomModelSerializer, TeacherShortProfileSerializer, \
    GroupStudentModelSerializer

from apps.serializers.management_serializers import (
    StudentListSerializer, StudentDetailSerializer,
    AttendanceSerializer, ParentShortSerializer, TeacherDetailSerializer, TeacherListSerializer
)
from apps.serializers.profile_serializers import StudentProfileSerializer, \
    AdminProfileSerializer
