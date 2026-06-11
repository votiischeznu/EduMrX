from django.urls import include, path
from rest_framework.routers import SimpleRouter

from apps.views import (
    AccountRecoveryViewSet,
    AdminDashboardView,
    GroupModelViewSet,
    GroupStudentModelViewSet,
    LoginAPIView,
    ManagementAttendanceViewSet,
    ManagementStudentDetailView,
    ManagementStudentListCreateView,
    ManagementTeacherDetailView,
    ManagementTeacherListCreateView,
    MyProfileRetrieveUpdateAPIView,
    RegisterCreateAPIView,
    RegisterVerifyAPIView,
    RoomModelViewSet,
    StudentDashboardView,
    StudentStatsView,
    SuperAdminCenterDetailView,
    SuperAdminCenterListCreateView,
    SuperAdminDashboardView,
    SuperAdminDirectorDetailView,
    SuperAdminDirectorListCreateView,
    SuperAdminFinanceCentersView,
    SuperAdminFinanceChartView,
    SuperAdminFinanceSummaryView,
    SuperAdminFinanceTransactionsView,
    SuperAdminStudentCenterListView,
    SuperAdminStudentDetailView,
    SuperAdminStudentListCreateView,
    UserViewSet,
)

# ── ROUTERS ──────────────────────────────────────────────────────────────────
router = SimpleRouter(trailing_slash=True)
router.register("rooms", RoomModelViewSet, basename="rooms")
router.register("groups", GroupModelViewSet, basename="groups")
router.register("group_students", GroupStudentModelViewSet, basename="group_students")
router.register("attendances", ManagementAttendanceViewSet, basename="management-attendance")
router.register(r"users", UserViewSet, basename="user")
router = SimpleRouter(trailing_slash=False)
router.register("recovery", AccountRecoveryViewSet, basename="auth-recovery")

urlpatterns = [
    # ── Auth alias ────────────────────────────────────────
    path("auth/login/", LoginAPIView.as_view()),
    path("auth/register/", RegisterCreateAPIView.as_view()),
    path("auth/register/verify/", RegisterVerifyAPIView.as_view()),
    path("auth/", include(router.urls)),
    # ── Profile ───────────────────────────────────────────
    path("me/", MyProfileRetrieveUpdateAPIView.as_view()),
    # ── Management Student ────────────────────────────────
    path("students/stats/", StudentStatsView.as_view(), name="student-stats"),
    path("students/", ManagementStudentListCreateView.as_view()),
    path("students/<uuid:pk>/", ManagementStudentDetailView.as_view()),
    # ── Management Teacher ────────────────────────────────
    path("teachers/", ManagementTeacherListCreateView.as_view()),
    path("teachers/<uuid:pk>/", ManagementTeacherDetailView.as_view()),
    # ── Dashboards ────────────────────────────────────────
    path("student/dashboard/", StudentDashboardView.as_view()),
    path("admin/dashboard/", AdminDashboardView.as_view()),



    path( "super-admin/dashboard/", SuperAdminDashboardView.as_view(), name="superadmin-dashboard"),
    path("super-admin/directors/",  SuperAdminDirectorListCreateView.as_view(), name="superadmin-director-list"),
    path("super-admin/directors/<uuid:pk>/", SuperAdminDirectorDetailView.as_view(), name="superadmin-director-detail"),

    path("super-admin/students/centers/",  SuperAdminStudentCenterListView.as_view(), name="superadmin-student-centers"),
    path("super-admin/students/", SuperAdminStudentListCreateView.as_view(), name="superadmin-student-list"),
    path("super-admin/students/<uuid:pk>/", SuperAdminStudentDetailView.as_view(), name="superadmin-student-detail"),

    path("super-admin/centers/", SuperAdminCenterListCreateView.as_view(), name="superadmin-center-list"),
    path("super-admin/centers/<uuid:pk>/",  SuperAdminCenterDetailView.as_view(), name="superadmin-center-detail"),

    path("super-admin/finance/summary/",  SuperAdminFinanceSummaryView.as_view(), name="superadmin-finance-summary"),
    path("super-admin/finance/chart/",  SuperAdminFinanceChartView.as_view(), name="superadmin-finance-chart"),
    path("super-admin/finance/centers/",  SuperAdminFinanceCentersView.as_view(), name="superadmin-finance-centers"),
    path("super-admin/finance/transactions/",  SuperAdminFinanceTransactionsView.as_view(), name="superadmin-finance-transactions"),
    path("", include(router.urls)),
]
