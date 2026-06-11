from apps.views.auth_views import (
    AccountRecoveryViewSet,
    LoginAPIView,
    RegisterCreateAPIView,
    RegisterVerifyAPIView,
)
from apps.views.dashboard_views import (
    AdminDashboardView,
    StudentDashboardView,
    StudentStatsView,
)
from apps.views.management_views import (
    ManagementAttendanceViewSet,
    ManagementStudentDetailView,
    ManagementStudentListCreateView,
    ManagementTeacherDetailView,
    ManagementTeacherListCreateView,
)
from apps.views.payment_views import (
    SuperAdminFinanceCentersView,
    SuperAdminFinanceChartView,
    SuperAdminFinanceSummaryView,
    SuperAdminFinanceTransactionsView,
)
from apps.views.super_admin_views import (
    SuperAdminCenterDetailView,
    SuperAdminCenterListCreateView,
    SuperAdminDashboardView,
    SuperAdminDirectorDetailView,
    SuperAdminDirectorListCreateView,
    SuperAdminStudentCenterListView,
    SuperAdminStudentDetailView,
    SuperAdminStudentListCreateView,
)
from apps.views.users import UserViewSet
from apps.views.views import (
    GroupModelViewSet,
    GroupStudentModelViewSet,
    MyProfileRetrieveUpdateAPIView,
    RoomModelViewSet,
)
