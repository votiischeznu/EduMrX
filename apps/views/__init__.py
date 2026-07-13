from apps.views.auth import (
    AccountRecoveryViewSet,
    LoginAPIView,
    RegisterCreateAPIView,
    RegisterVerifyAPIView,
    TelegramOAuthView
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
    SuperAdminStudentDetailView)
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
    DirectorAdminListCreateView,
    DirectorAdminDetailView,
    DirectorAnalyticsSummaryView,
    DirectorAnalyticsChartView,
    DirectorAnalyticsTransactionsView,
    DirectorAnalyticsBranchesView,
    DirectorAnalyticsBranchTabsView
)
from apps.views.center import BranchDetailView, BranchListCreateView


from apps.views.manager import (
    ManagerAttendanceView,
    ManagerCourseDetailView,
    ManagerCourseListCreateView,
    ManagerDashboardView,
    ManagerGroupDetailView,
    ManagerGroupEnrollView,
    ManagerGroupListCreateView,
    ManagerLessonDetailView,
    ManagerLessonListCreateView,
    ManagerPaymentListView,
    ManagerRoomDetailView,
    ManagerRoomListCreateView,
    ManagerStudentDetailView,
    ManagerStudentListCreateView,
    ManagerTeacherDetailView,
    ManagerTeacherListCreateView,
)

from apps.views.notifications import (
    ContactMessageCreateView,
    SuperAdminContactMessageListView,
    SuperAdminContactMessageMarkReadView,
    DirectorSendNotificationView,
    ManagerSendNotificationView
)

from apps.views.telegram_link import TelegramLinkStartView, TelegramLinkStatusView

from apps.views.super_admin import SuperAdminStudentListView
from apps.views.telegram_webhook import telegram_webhook