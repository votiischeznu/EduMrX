from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.views import (
    MyProfileRetrieveUpdateAPIView, RoomModelViewSet,
    GroupModelViewSet, GroupStudentModelViewSet,
    RegisterModelViewSet, AccountRecoveryViewSet, LoginAPIView,
    ManagementAttendanceViewSet, ManagementStudentDetailView, ManagementTeacherDetailView,
)
from apps.views.management_views import ManagementStudentListCreateView, ManagementTeacherListCreateView
from apps.views.student_views import AdminDashboardView, StudentDashboardView, StudentStatsView
from apps.views.super_admin_views import (
    SuperAdminDashboardView,
    SuperAdminStudentListCreateView, SuperAdminStudentDetailView,
    SuperAdminTeacherListCreateView, SuperAdminTeacherDetailView,
    SuperAdminCenterListCreateView, SuperAdminCenterDetailView,
    SuperAdminDirectorListCreateView, SuperAdminDirectorDetailView,
)
from apps.views import (
    MyProfileRetrieveUpdateAPIView, RoomModelViewSet,
    GroupModelViewSet, GroupStudentModelViewSet,
    RegisterModelViewSet, AccountRecoveryViewSet, LoginAPIView,
    ManagementAttendanceViewSet, ManagementStudentDetailView, ManagementTeacherDetailView,
)
from apps.views.management_views import ManagementStudentListCreateView, ManagementTeacherListCreateView
from apps.views.student_views import AdminDashboardView, StudentDashboardView
from apps.views.super_admin_views import (
    SuperAdminDashboardView,
    SuperAdminStudentListCreateView, SuperAdminStudentDetailView,
    SuperAdminTeacherListCreateView, SuperAdminTeacherDetailView,
    SuperAdminCenterListCreateView, SuperAdminCenterDetailView,
    SuperAdminDirectorListCreateView, SuperAdminDirectorDetailView,
)

# ── ROUTERS ──────────────────────────────────────────────────────────────────
api_router = SimpleRouter(trailing_slash=True)
api_router.register('rooms', RoomModelViewSet, basename='rooms')
api_router.register('groups', GroupModelViewSet, basename='groups')
api_router.register('group_students', GroupStudentModelViewSet, basename='group_students')
api_router.register('attendances', ManagementAttendanceViewSet, basename='management-attendance')

auth_router = SimpleRouter(trailing_slash=False)
auth_router.register('register', RegisterModelViewSet, basename='auth-register')
auth_router.register('recovery', AccountRecoveryViewSet, basename='auth-recovery')

# ── URL PATTERNS ─────────────────────────────────────────────────────────────
urlpatterns = [
    # ── Core API Services ─────────────────────────────────────────────────────
    path('api/v1/', include([

        # ── Auth ─────────────────────────────────────────────────────────────────
        path('auth/', include([
            path('', include(auth_router.urls)),
            path('login/', LoginAPIView.as_view()),
            path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
            path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        ])),

        # ── Auth alias ────────────────────────────────────────
        path('auth/login/', LoginAPIView.as_view()),
        path('auth/token/', TokenObtainPairView.as_view()),
        path('auth/token/refresh/', TokenRefreshView.as_view()),
        path('auth/', include(auth_router.urls)),

        # ── Profile ───────────────────────────────────────────
        path('me/', MyProfileRetrieveUpdateAPIView.as_view()),

        # ── Management ────────────────────────────────────────
        path('students/', ManagementStudentListCreateView.as_view()),
        path('students/<uuid:pk>/', ManagementStudentDetailView.as_view()),
        path('teachers/', ManagementTeacherListCreateView.as_view()),
        path('teachers/<uuid:pk>/', ManagementTeacherDetailView.as_view()),

        # ── Dashboards ────────────────────────────────────────
        path('student/dashboard/', StudentDashboardView.as_view()),
        path('admin/dashboard/', AdminDashboardView.as_view()),

        # ── Super Admin ───────────────────────────────────────
        path('super-admin/dashboard/', SuperAdminDashboardView.as_view()),
        path('super-admin/directors/', SuperAdminDirectorListCreateView.as_view()),
        path('super-admin/directors/<uuid:pk>/', SuperAdminDirectorDetailView.as_view()),
        path('super-admin/centers/', SuperAdminCenterListCreateView.as_view()),
        path('super-admin/centers/<uuid:pk>/', SuperAdminCenterDetailView.as_view()),
        path('super-admin/students/', SuperAdminStudentListCreateView.as_view()),
        path('super-admin/students/<uuid:pk>/', SuperAdminStudentDetailView.as_view()),
        path('super-admin/teachers/', SuperAdminTeacherListCreateView.as_view()),
        path('super-admin/teachers/<uuid:pk>/', SuperAdminTeacherDetailView.as_view()),

        # ── ViewSet Router ────────────────────────────────────
        path('', include(api_router.urls)),
    ])),
    # ── Auth ─────────────────────────────────────────────────────────────────
    path('auth/', include([
        path('', include(auth_router.urls)),
        path('login/', LoginAPIView.as_view()),
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ])),

    # ── Auth alias ────────────────────────────────────────
    path('auth/login/', LoginAPIView.as_view()),
    path('auth/token/', TokenObtainPairView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/', include(auth_router.urls)),

    # ── Profile ───────────────────────────────────────────
    path('me/', MyProfileRetrieveUpdateAPIView.as_view()),

    # ── Management Student ────────────────────────────────────────
    path("students/stats/", StudentStatsView.as_view(), name="student-stats"),
    path('students/', ManagementStudentListCreateView.as_view()),
    path('students/<uuid:pk>/', ManagementStudentDetailView.as_view()),

    # ── Management Teacher ────────────────────────────────────────
    path('teachers/', ManagementTeacherListCreateView.as_view()),
    path('teachers/<uuid:pk>/', ManagementTeacherDetailView.as_view()),

    # ── Dashboards ────────────────────────────────────────
    path('student/dashboard/', StudentDashboardView.as_view()),
    path('admin/dashboard/', AdminDashboardView.as_view()),

    # ── Super Admin ───────────────────────────────────────
    path('super-admin/dashboard/', SuperAdminDashboardView.as_view()),
    path('super-admin/directors/', SuperAdminDirectorListCreateView.as_view()),
    path('super-admin/directors/<uuid:pk>/', SuperAdminDirectorDetailView.as_view()),
    path('super-admin/centers/', SuperAdminCenterListCreateView.as_view()),
    path('super-admin/centers/<uuid:pk>/', SuperAdminCenterDetailView.as_view()),
    path('super-admin/students/', SuperAdminStudentListCreateView.as_view()),
    path('super-admin/students/<uuid:pk>/', SuperAdminStudentDetailView.as_view()),
    path('super-admin/teachers/', SuperAdminTeacherListCreateView.as_view()),
    path('super-admin/teachers/<uuid:pk>/', SuperAdminTeacherDetailView.as_view()),

    # ── ViewSet Router ────────────────────────────────────
    path('', include(api_router.urls)),
]