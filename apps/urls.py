from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.views import (
    MyProfileRetrieveUpdateAPIView,
    RoomModelViewSet,
    GroupModelViewSet,
    GroupStudentModelViewSet,
    AccountRecoveryViewSet,
    LoginAPIView,
    ManagementAttendanceViewSet,
    ManagementStudentDetailView,
    ManagementTeacherDetailView,
    RegisterCreateAPIView,
    RegisterVerifyAPIView,
    StudentStatsView,
    ManagementStudentListCreateView,
    ManagementTeacherListCreateView,
    StudentDashboardView,
    AdminDashboardView,
    SuperAdminDashboardView,
    SuperAdminDirectorListCreateView,
    SuperAdminDirectorDetailView,
    SuperAdminCenterListCreateView,
    SuperAdminCenterDetailView,
    SuperAdminStudentCenterListView,
)
from apps.views.payment_views import (
    SuperAdminFinanceTransactionsView,
    SuperAdminFinanceCentersView,
    SuperAdminFinanceChartView,
    SuperAdminFinanceSummaryView,
)
from apps.views.super_admin_views import (
    SuperAdminStudentListCreateView,
    SuperAdminStudentDetailView,
)
from apps.views.users import UserViewSet

# ── ROUTERS ──────────────────────────────────────────────────────────────────
api_router = SimpleRouter(trailing_slash=True)
api_router.register("rooms", RoomModelViewSet, basename="rooms")
api_router.register("groups", GroupModelViewSet, basename="groups")
api_router.register(
    "group_students", GroupStudentModelViewSet, basename="group_students"
)
api_router.register(
    "attendances", ManagementAttendanceViewSet, basename="management-attendance"
)
api_router.register(r"users", UserViewSet, basename="user")

auth_router = SimpleRouter(trailing_slash=False)
auth_router.register("recovery", AccountRecoveryViewSet, basename="auth-recovery")

urlpatterns = [
    # ── Auth alias ────────────────────────────────────────
    path("auth/login/", LoginAPIView.as_view()),
    path("auth/register/", RegisterCreateAPIView.as_view()),
    path("auth/register/verify/", RegisterVerifyAPIView.as_view()),
    path("auth/", include(auth_router.urls)),
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
    path(
        "super-admin/dashboard/",
        SuperAdminDashboardView.as_view(),
        name="superadmin-dashboard",
    ),
    # ── Director ───────────────────────────────────────────────
    path(
        "super-admin/directors/",
        SuperAdminDirectorListCreateView.as_view(),
        name="superadmin-director-list",
    ),
    path(
        "super-admin/directors/<uuid:pk>/",
        SuperAdminDirectorDetailView.as_view(),
        name="superadmin-director-detail",
    ),
    # ── Student ────────────────────────────────────────────────
    path(
        "super-admin/students/centers/",
        SuperAdminStudentCenterListView.as_view(),
        name="superadmin-student-centers",
    ),
    path(
        "super-admin/students/",
        SuperAdminStudentListCreateView.as_view(),
        name="superadmin-student-list",
    ),
    path(
        "super-admin/students/<uuid:pk>/",
        SuperAdminStudentDetailView.as_view(),
        name="superadmin-student-detail",
    ),
    # ── Center ─────────────────────────────────────────────────
    path(
        "super-admin/centers/",
        SuperAdminCenterListCreateView.as_view(),
        name="superadmin-center-list",
    ),
    path(
        "super-admin/centers/<uuid:pk>/",
        SuperAdminCenterDetailView.as_view(),
        name="superadmin-center-detail",
    ),
    # ── Finance ────────────────────────────────────────────────
    path(
        "super-admin/finance/summary/",
        SuperAdminFinanceSummaryView.as_view(),
        name="superadmin-finance-summary",
    ),
    path(
        "super-admin/finance/chart/",
        SuperAdminFinanceChartView.as_view(),
        name="superadmin-finance-chart",
    ),
    path(
        "super-admin/finance/centers/",
        SuperAdminFinanceCentersView.as_view(),
        name="superadmin-finance-centers",
    ),
    path(
        "super-admin/finance/transactions/",
        SuperAdminFinanceTransactionsView.as_view(),
        name="superadmin-finance-transactions",
    ),
    path("", include(api_router.urls)),
]
