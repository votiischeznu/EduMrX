from apps.serializers.auth import (
    LoginModelSerializer,
    RegisterModelSerializer,
    TelegramOAuthSerializer
)
from apps.serializers.auth import (
    RecoveryStartSerializer,
    RecoveryVerifySerializer,
    RecoveryCompleteSerializer,
)

from apps.serializers.group import (
    GroupModelSerializer,
    RoomModelSerializer,
    TeacherShortProfileSerializer,
    GroupStudentModelSerializer,
)

from apps.serializers.management import (
    StudentListSerializer,
    StudentDetailSerializer,
    AttendanceSerializer,
    ParentShortSerializer,
    TeacherDetailSerializer,
    TeacherListSerializer,
    StudentCreateUpdateSerializer,
    TeacherCreateUpdateSerializer,
)
from apps.serializers.profile import (
    StudentProfileSerializer,
    AdminProfileSerializer,
    TeacherProfileSerializer,
    ParentProfileSerializer,
)
from apps.serializers.super_admin import (
    CenterListSerializer,
    CenterDetailSerializer,
    DirectorCreateUpdateSerializer,
    DirectorListSerializer,
)

from apps.serializers.super_admin import (
    SuperAdminMenuStatsSerializer,
    CenterStudentCountSerializer,
)

from apps.serializers.director import (
    DirectorTeacherCreateSerializer,
    DirectorTeacherDetailSerializer,
    DirectorTeacherListSerializer,
    DirectorRoomSerializer,
    DirectorCourseSerializer,
    DirectorGroupCreateSerializer,
    DirectorGroupEnrollSerializer,
    DirectorGroupListSerializer,
    DirectorLessonCreateSerializer,
    DirectorLessonListSerializer,
    DirectorAttendanceBulkSerializer,
    DirectorAttendanceSerializer,
    DirectorStudentCreateSerializer,
    DirectorStudentDetailSerializer,
    DirectorStudentListSerializer,
    DirectorAdminCreateSerializer,
    DirectorAdminDetailSerializer,
    DirectorAdminListSerializer,
    DirectorGroupCreateSerializer
)

from apps.serializers.manager import (
    ManagerStudentListSerializer,
    ManagerStudentDetailSerializer,
    ManagerStudentCreateSerializer,
    ManagerTeacherListSerializer,
    ManagerTeacherDetailSerializer,
    ManagerTeacherCreateSerializer,
    ManagerGroupCreateSerializer,
    ManagerPaymentSerializer,
)
from apps.serializers.notifications import ContactMessageCreateSerializer, ContactMessageListSerializer, \
    ContactMessageMarkReadSerializer
