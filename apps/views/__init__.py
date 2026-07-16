from apps.views.auth import (
    AccountRecoveryViewSet,
    LoginAPIView,
    RegisterCreateAPIView,
    RegisterVerifyAPIView,
    TelegramOAuthView
)
from apps.views.dashboard import (
    AdminDashboardView,
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
    ManagerRoomDetailView,
    ManagerRoomListCreateView,
    ManagerStudentDetailView,
    ManagerStudentListCreateView,
    ManagerTeacherDetailView,
    ManagerTeacherListCreateView,
    ManagerPaymentListCreateView
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
from apps.views.teacher import TeacherGroupViewSet, TeacherSalaryView, TeacherLessonViewSet

from apps.views.finance import (
    DebtListCreateView,
    ExpenseCategoryDetailView,
    ExpenseCategoryListCreateView,
    ExpenseDetailView,
    ExpenseListCreateView,
    ExpenseSummaryView,
    PaymentDetailView,
    PaymentListCreateView,
    PaymentSummaryView,
    StudentPaymentListView,
)
from apps.views.student import StudentAttendanceListView, StudentDashboardView
