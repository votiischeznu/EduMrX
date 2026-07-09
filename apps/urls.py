# apps/urls.py
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.views import (
    AccountRecoveryViewSet,
    AdminDashboardView,
    BranchDetailView,
    BranchListCreateView,
    ContactMessageCreateView,
    DirectorAdminDetailView,
    DirectorAdminListCreateView,
    DirectorAnalyticsBranchesView,
    DirectorAnalyticsBranchTabsView,
    DirectorAnalyticsChartView,
    DirectorAnalyticsSummaryView,
    DirectorAnalyticsTransactionsView,
    DirectorAttendanceView,
    DirectorCourseDetailView,
    DirectorCourseListCreateView,
    DirectorDashboardView,
    DirectorGroupDetailView,
    DirectorGroupEnrollView,
    DirectorGroupListCreateView,
    DirectorLessonDetailView,
    DirectorLessonListCreateView,
    DirectorRoomDetailView,
    DirectorRoomListCreateView,
    DirectorSendNotificationView,
    DirectorStudentDetailView,
    DirectorStudentListCreateView,
    DirectorTeacherDetailView,
    DirectorTeacherListCreateView,
    GroupModelViewSet,
    GroupStudentModelViewSet,
    LoginAPIView,
    ManagementAttendanceViewSet,
    ManagementStudentDetailView,
    ManagementStudentListCreateView,
    ManagementTeacherDetailView,
    ManagementTeacherListCreateView,
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
    ManagerSendNotificationView,
    ManagerStudentDetailView,
    ManagerStudentListCreateView,
    ManagerTeacherDetailView,
    ManagerTeacherListCreateView,
    MyProfileRetrieveUpdateAPIView,
    RegisterCreateAPIView,
    RegisterVerifyAPIView,
    RoomModelViewSet,
    StudentDashboardView,
    StudentStatsView,
    SuperAdminCenterDetailView,
    SuperAdminCenterListCreateView,
    SuperAdminCenterStudentListView,
    SuperAdminContactMessageListView,
    SuperAdminContactMessageMarkReadView,
    SuperAdminDashboardView,
    SuperAdminDirectorDetailView,
    SuperAdminDirectorListCreateView,
    SuperAdminFinanceCentersView,
    SuperAdminFinanceChartView,
    SuperAdminFinanceSummaryView,
    SuperAdminFinanceTransactionsView,
    SuperAdminStudentDetailView,
    SuperAdminStudentListView,
    TelegramLinkStartView,
    TelegramLinkStatusView,
    TelegramOAuthView,
)
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

main_router = SimpleRouter(trailing_slash=True)
main_router.register("rooms", RoomModelViewSet, basename="rooms")
main_router.register("groups", GroupModelViewSet, basename="groups")
main_router.register("group_students", GroupStudentModelViewSet, basename="group_students")
main_router.register("attendances", ManagementAttendanceViewSet, basename="management-attendance")
auth_router = SimpleRouter(trailing_slash=False)
auth_router.register("recovery", AccountRecoveryViewSet, basename="auth-recovery")


urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/register/", RegisterCreateAPIView.as_view(), name="auth-register"),
    path("auth/register/verify/", RegisterVerifyAPIView.as_view(), name="auth-register-verify"),
    path("auth/", include(auth_router.urls)),
    path("auth/telegram/", TelegramOAuthView.as_view(), name="auth-telegram"),
    # ── Main Router ───────────────────────────────────────
    path("", include(main_router.urls)),
    # ── Profile ───────────────────────────────────────────
    path("me/", MyProfileRetrieveUpdateAPIView.as_view(), name="my-profile"),
    # ── Management: Students ──────────────────────────────
    path("students/stats/", StudentStatsView.as_view(), name="students-stats"),
    path("students/", ManagementStudentListCreateView.as_view(), name="students-list-create"),
    path("students/<uuid:pk>/", ManagementStudentDetailView.as_view(), name="students-detail"),
    # ── Management: Teachers ──────────────────────────────
    path("teachers/", ManagementTeacherListCreateView.as_view(), name="teachers-list-create"),
    path("teachers/<uuid:pk>/", ManagementTeacherDetailView.as_view(), name="teachers-detail"),
    # ── Dashboards ────────────────────────────────────────
    path("student/dashboard/", StudentDashboardView.as_view(), name="student-dashboard"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    # ── Super Admin ───────────────────────────────────────
    path("super-admin/dashboard/", SuperAdminDashboardView.as_view(), name="super-admin-dashboard"),
    path(
        "super-admin/directors/", SuperAdminDirectorListCreateView.as_view(), name="super-admin-directors-list-create"
    ),
    path(
        "super-admin/directors/<uuid:pk>/", SuperAdminDirectorDetailView.as_view(), name="super-admin-directors-detail"
    ),
    path(
        "super-admin/center/student/stats/",
        SuperAdminCenterStudentListView.as_view(),
        name="super-admin-center-student-stats",
    ),
    path("super-admin/centers/", SuperAdminCenterListCreateView.as_view(), name="super-admin-centers-list-create"),
    path("super-admin/centers/<uuid:pk>/", SuperAdminCenterDetailView.as_view(), name="super-admin-centers-detail"),
    path("super-admin/students/", SuperAdminStudentListView.as_view(), name="super-admin-students-list"),
    path("super-admin/students/<uuid:pk>/", SuperAdminStudentDetailView.as_view(), name="super-admin-students-detail"),
    path("super-admin/finance/summary/", SuperAdminFinanceSummaryView.as_view(), name="super-admin-finance-summary"),
    path("super-admin/finance/chart/", SuperAdminFinanceChartView.as_view(), name="super-admin-finance-chart"),
    path("super-admin/finance/centers/", SuperAdminFinanceCentersView.as_view(), name="super-admin-finance-centers"),
    path(
        "super-admin/finance/transactions/",
        SuperAdminFinanceTransactionsView.as_view(),
        name="super-admin-finance-transactions",
    ),
    path("contact/", ContactMessageCreateView.as_view(), name="contact-create"),
    path("superadmin/contact/", SuperAdminContactMessageListView.as_view(), name="super-admin-contact-list"),
    path(
        "superadmin/contact/<int:pk>/mark-read/",
        SuperAdminContactMessageMarkReadView.as_view(),
        name="super-admin-contact-mark-read",
    ),
    # ── Director ──────────────────────────────────────────
    path("director/dashboard/", DirectorDashboardView.as_view(), name="director-dashboard"),
    path("director/admins/", DirectorAdminListCreateView.as_view(), name="director-admins-list-create"),
    path("director/admins/<uuid:pk>/", DirectorAdminDetailView.as_view(), name="director-admins-detail"),
    # Students
    path("director/students/", DirectorStudentListCreateView.as_view(), name="director-students-list-create"),
    path("director/students/<uuid:pk>/", DirectorStudentDetailView.as_view(), name="director-students-detail"),
    # Teachers
    path("director/teachers/", DirectorTeacherListCreateView.as_view(), name="director-teachers-list-create"),
    path("director/teachers/<uuid:pk>/", DirectorTeacherDetailView.as_view(), name="director-teachers-detail"),
    # Rooms
    path("director/rooms/", DirectorRoomListCreateView.as_view(), name="director-rooms-list-create"),
    path("director/rooms/<uuid:pk>/", DirectorRoomDetailView.as_view(), name="director-rooms-detail"),
    # Courses
    path("director/courses/", DirectorCourseListCreateView.as_view(), name="director-courses-list-create"),
    path("director/courses/<uuid:pk>/", DirectorCourseDetailView.as_view(), name="director-courses-detail"),
    # Groups
    path("director/groups/", DirectorGroupListCreateView.as_view(), name="director-groups-list-create"),
    path("director/groups/<uuid:pk>/", DirectorGroupDetailView.as_view(), name="director-groups-detail"),
    path("director/groups/<uuid:pk>/enroll/", DirectorGroupEnrollView.as_view(), name="director-groups-enroll"),
    # Lessons
    path("director/lessons/", DirectorLessonListCreateView.as_view(), name="director-lessons-list-create"),
    path("director/lessons/<uuid:pk>/", DirectorLessonDetailView.as_view(), name="director-lessons-detail"),
    path(
        "director/lessons/<uuid:pk>/attendance/", DirectorAttendanceView.as_view(), name="director-lessons-attendance"
    ),
    path("director/analytics/summary/", DirectorAnalyticsSummaryView.as_view(), name="director-analytics-summary"),
    path("director/analytics/chart/", DirectorAnalyticsChartView.as_view(), name="director-analytics-chart"),
    path(
        "director/analytics/transactions/",
        DirectorAnalyticsTransactionsView.as_view(),
        name="director-analytics-transactions",
    ),
    path("director/analytics/centers/", DirectorAnalyticsBranchesView.as_view(), name="director-analytics-centers"),
    path("director/analytics/branches/", DirectorAnalyticsBranchTabsView.as_view(), name="director-analytics-branches"),
    # ── Manager ──────────────────────────────────────────
    path("manager/dashboard/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    # Students
    path("manager/students/", ManagerStudentListCreateView.as_view(), name="manager-students-list-create"),
    path("manager/students/<uuid:pk>/", ManagerStudentDetailView.as_view(), name="manager-students-detail"),
    # Teachers
    path("manager/teachers/", ManagerTeacherListCreateView.as_view(), name="manager-teachers-list-create"),
    path("manager/teachers/<uuid:pk>/", ManagerTeacherDetailView.as_view(), name="manager-teachers-detail"),
    # Rooms
    path("manager/rooms/", ManagerRoomListCreateView.as_view(), name="manager-rooms-list-create"),
    path("manager/rooms/<uuid:pk>/", ManagerRoomDetailView.as_view(), name="manager-rooms-detail"),
    # Courses
    path("manager/courses/", ManagerCourseListCreateView.as_view(), name="manager-courses-list-create"),
    path("manager/courses/<uuid:pk>/", ManagerCourseDetailView.as_view(), name="manager-courses-detail"),
    # Groups
    path("manager/groups/", ManagerGroupListCreateView.as_view(), name="manager-groups-list-create"),
    path("manager/groups/<uuid:pk>/", ManagerGroupDetailView.as_view(), name="manager-groups-detail"),
    path("manager/groups/<uuid:pk>/enroll/", ManagerGroupEnrollView.as_view(), name="manager-groups-enroll"),
    # Lessons
    path("manager/lessons/", ManagerLessonListCreateView.as_view(), name="manager-lessons-list-create"),
    path("manager/lessons/<uuid:pk>/", ManagerLessonDetailView.as_view(), name="manager-lessons-detail"),
    # Attendance
    path("manager/lessons/<uuid:pk>/attendance/", ManagerAttendanceView.as_view(), name="manager-lessons-attendance"),
    # Payments
    path("manager/payments/", ManagerPaymentListView.as_view(), name="manager-payments-list"),
    path("center/branches/", BranchListCreateView.as_view(), name="branches-list-create"),
    path("center/branches/<uuid:pk>/", BranchDetailView.as_view(), name="branches-detail"),
    # telegram
    path("telegram/link/start/", TelegramLinkStartView.as_view(), name="telegram-link-start"),
    path("telegram/link/status/", TelegramLinkStatusView.as_view(), name="telegram-link-status"),
    path("manager/notifications/send/", ManagerSendNotificationView.as_view(), name="manager-notifications-send"),
    path("director/notifications/send/", DirectorSendNotificationView.as_view(), name="director-notifications-send"),
    path("expense-categories/", ExpenseCategoryListCreateView.as_view(), name="expense-categories-list-create"),
    path("expense-categories/<uuid:pk>/", ExpenseCategoryDetailView.as_view(), name="expense-categories-detail"),
    path("expenses/", ExpenseListCreateView.as_view(), name="expenses-list-create"),
    path("expenses/summary/", ExpenseSummaryView.as_view(), name="expenses-summary"),
    path("expenses/<uuid:pk>/", ExpenseDetailView.as_view(), name="expenses-detail"),
    path("payments/", PaymentListCreateView.as_view(), name="payments-list-create"),
    path("payments/summary/", PaymentSummaryView.as_view(), name="payments-summary"),
    path("payments/<uuid:pk>/", PaymentDetailView.as_view(), name="payments-detail"),
    # O'quvchi to'lov tarixi
    path("students/<uuid:student_id>/payments/", StudentPaymentListView.as_view(), name="student-payments-list"),
    # Qarzlar
    path("debts/", DebtListCreateView.as_view(), name="debts-list-create"),
]
