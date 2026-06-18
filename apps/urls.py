# apps/urls.py
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
    SuperAdminStudentDetailView,
    SuperAdminStudentListCreateView,
    SuperAdminCenterStudentListView,
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
from apps.views.manager import (
    ManagerPaymentListView,
    ManagerDashboardView,
    ManagerStudentListCreateView,
    ManagerStudentDetailView,
    ManagerTeacherListCreateView,
    ManagerTeacherDetailView,
    ManagerRoomListCreateView,
    ManagerRoomDetailView,
    ManagerCourseListCreateView,
    ManagerCourseDetailView,
    ManagerGroupListCreateView,
    ManagerGroupDetailView,
    ManagerGroupEnrollView,
    ManagerLessonListCreateView,
    ManagerLessonDetailView,
    ManagerAttendanceView,
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
    path("auth/login/", LoginAPIView.as_view()),
    path("auth/register/", RegisterCreateAPIView.as_view()),
    path("auth/register/verify/", RegisterVerifyAPIView.as_view()),
    path("auth/", include(auth_router.urls)),
    # ── Main Router ───────────────────────────────────────
    path("", include(main_router.urls)),
    # ── Profile ───────────────────────────────────────────
    path("me/", MyProfileRetrieveUpdateAPIView.as_view()),
    # ── Management: Students ──────────────────────────────
    path("students/stats/", StudentStatsView.as_view()),
    path("students/", ManagementStudentListCreateView.as_view()),
    path("students/<uuid:pk>/", ManagementStudentDetailView.as_view()),
    # ── Management: Teachers ──────────────────────────────
    path("teachers/", ManagementTeacherListCreateView.as_view()),
    path("teachers/<uuid:pk>/", ManagementTeacherDetailView.as_view()),
    # ── Dashboards ────────────────────────────────────────
    path("student/dashboard/", StudentDashboardView.as_view()),
    path("admin/dashboard/", AdminDashboardView.as_view()),
    # ── Super Admin ───────────────────────────────────────
    path("super-admin/dashboard/", SuperAdminDashboardView.as_view()),
    path("super-admin/directors/", SuperAdminDirectorListCreateView.as_view()),
    path("super-admin/directors/<uuid:pk>/", SuperAdminDirectorDetailView.as_view()),
    path("super-admin/students/", SuperAdminStudentListCreateView.as_view()),
    path("super-admin/students/<uuid:pk>/", SuperAdminStudentDetailView.as_view()),
    path(
        "super-admin/center/student/stats/", SuperAdminCenterStudentListView.as_view()
    ),
    path("super-admin/centers/", SuperAdminCenterListCreateView.as_view()),
    path("super-admin/centers/<uuid:pk>/", SuperAdminCenterDetailView.as_view()),
    path("super-admin/finance/summary/", SuperAdminFinanceSummaryView.as_view()),
    path("super-admin/finance/chart/", SuperAdminFinanceChartView.as_view()),
    path("super-admin/finance/centers/", SuperAdminFinanceCentersView.as_view()),
    path(
        "super-admin/finance/transactions/", SuperAdminFinanceTransactionsView.as_view()
    ),
    # ── Director ──────────────────────────────────────────
    path("director/dashboard/", DirectorDashboardView.as_view()),
    # Students
    path("director/students/", DirectorStudentListCreateView.as_view()),
    path("director/students/<uuid:pk>/", DirectorStudentDetailView.as_view()),
    # Teachers
    path("director/teachers/", DirectorTeacherListCreateView.as_view()),
    path("director/teachers/<uuid:pk>/", DirectorTeacherDetailView.as_view()),
    # Rooms
    path("director/rooms/", DirectorRoomListCreateView.as_view()),
    path("director/rooms/<uuid:pk>/", DirectorRoomDetailView.as_view()),
    # Courses
    path("director/courses/", DirectorCourseListCreateView.as_view()),
    path("director/courses/<uuid:pk>/", DirectorCourseDetailView.as_view()),
    # Groups
    path("director/groups/", DirectorGroupListCreateView.as_view()),
    path("director/groups/<uuid:pk>/", DirectorGroupDetailView.as_view()),
    path("director/groups/<uuid:pk>/enroll/", DirectorGroupEnrollView.as_view()),
    # Lessons
    path("director/lessons/", DirectorLessonListCreateView.as_view()),
    path("director/lessons/<uuid:pk>/", DirectorLessonDetailView.as_view()),
    path("director/lessons/<uuid:pk>/attendance/", DirectorAttendanceView.as_view()),
    # ── Manager ──────────────────────────────────────────
    path("manager/dashboard/", ManagerDashboardView.as_view()),
    # Students
    path("manager/students/", ManagerStudentListCreateView.as_view()),
    path("manager/students/<uuid:pk>/", ManagerStudentDetailView.as_view()),
    # Teachers
    path("manager/teachers/", ManagerTeacherListCreateView.as_view()),
    path("manager/teachers/<uuid:pk>/", ManagerTeacherDetailView.as_view()),
    # Rooms
    path("manager/rooms/", ManagerRoomListCreateView.as_view()),
    path("manager/rooms/<uuid:pk>/", ManagerRoomDetailView.as_view()),
    # Courses
    path("manager/courses/", ManagerCourseListCreateView.as_view()),
    path("manager/courses/<uuid:pk>/", ManagerCourseDetailView.as_view()),
    # Groups
    path("manager/groups/", ManagerGroupListCreateView.as_view()),
    path("manager/groups/<uuid:pk>/", ManagerGroupDetailView.as_view()),
    path("manager/groups/<uuid:pk>/enroll/", ManagerGroupEnrollView.as_view()),
    # Lessons
    path("manager/lessons/", ManagerLessonListCreateView.as_view()),
    path("manager/lessons/<uuid:pk>/", ManagerLessonDetailView.as_view()),
    # Attendance
    path("manager/lessons/<uuid:pk>/attendance/", ManagerAttendanceView.as_view()),
    # Payments
    path("manager/payments/", ManagerPaymentListView.as_view()),
]
