from apps.views.auth import (
    AccountRecoveryViewSet,
    LoginAPIView,
    RegisterCreateAPIView,
    RegisterVerifyAPIView,
)
from apps.views.dashboard import (
    AdminDashboardView,
    StudentDashboardView,
    StudentStatsView,
)
from apps.views.management import (
    ManagementAttendanceViewSet,
    ManagementStudentDetailView,
    ManagementStudentListCreateView,
    ManagementTeacherDetailView,
    ManagementTeacherListCreateView,
)
from apps.views.payment import (
    SuperAdminFinanceCentersView,
    SuperAdminFinanceChartView,
    SuperAdminFinanceSummaryView,
    SuperAdminFinanceTransactionsView,
)
from apps.views.super_admin import (
    SuperAdminCenterDetailView,
    SuperAdminCenterListCreateView,
    SuperAdminCenterStudentListView,
    SuperAdminDashboardView,
    SuperAdminDirectorDetailView,
    SuperAdminDirectorListCreateView,
    SuperAdminStudentDetailView,
    SuperAdminStudentListCreateView,
)
from apps.views.profile import (
    GroupModelViewSet,
    GroupStudentModelViewSet,
    MyProfileRetrieveUpdateAPIView,
    RoomModelViewSet,
)

from apps.views.director import (
    DirectorAttendanceView,
    DirectorLessonDetailView,
    DirectorLessonListCreateView,
    DirectorGroupEnrollView,
    DirectorGroupDetailView,
    DirectorGroupListCreateView,
    DirectorCourseDetailView,
    DirectorRoomDetailView,
    DirectorCourseListCreateView,
    DirectorRoomListCreateView,
    DirectorTeacherListCreateView,
    DirectorTeacherDetailView,
    DirectorStudentDetailView,
    DirectorStudentListCreateView,
    DirectorDashboardView,
)
