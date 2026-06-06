from apps.views.auth_views import AccountRecoveryViewSet, LoginAPIView, RegisterCreateAPIView
from apps.views.auth_views import RegisterCreateAPIView, RegisterVerifyAPIView
from apps.views.dashboard_views import AdminDashboardView, StudentDashboardView
from apps.views.dashboard_views import AdminDashboardView, StudentDashboardView
from apps.views.dashboard_views import StudentStatsView
from apps.views.management_views import ManagementAttendanceViewSet, ManagementStudentDetailView, \
    ManagementStudentDetailView, ManagementTeacherDetailView, ManagementTeacherDetailView
from apps.views.management_views import ManagementStudentListCreateView, ManagementTeacherListCreateView
from apps.views.super_admin_views import (
    SuperAdminDashboardView,
    SuperAdminCenterListCreateView, SuperAdminCenterDetailView,
    SuperAdminDirectorListCreateView, SuperAdminDirectorDetailView, SuperAdminStudentCenterListView,

)
from apps.views.views import MyProfileRetrieveUpdateAPIView, RoomModelViewSet, GroupModelViewSet, \
    GroupStudentModelViewSet
