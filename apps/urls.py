from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.views import MyProfileRetrieveUpdateAPIView, RoomModelViewSet, GroupModelViewSet, GroupStudentModelViewSet, \
    RegisterModelViewSet, AccountRecoveryViewSet, LoginAPIView, ManagementAttendanceViewSet, ManagementStudentListView, \
    ManagementStudentDetailView, ManagementTeacherListView, ManagementTeacherDetailView
from apps.views.management_views import SuperAdminStudentListCreateView, SuperAdminStudentDetailView, \
    SuperAdminTeacherListCreateView, SuperAdminTeacherDetailView, SuperAdminCenterDetailView, \
    SuperAdminCenterListCreateView

api_router = SimpleRouter(trailing_slash=False)
api_router.register('rooms', RoomModelViewSet, basename='rooms')
api_router.register('groups', GroupModelViewSet, basename='groups')
api_router.register('group_students', GroupStudentModelViewSet, basename='group_students')
api_router.register(r'attendances', ManagementAttendanceViewSet, basename='management-attendance')

auth_router = SimpleRouter(trailing_slash=False)
auth_router.register('register', RegisterModelViewSet, basename='auth-register')
auth_router.register('recovery', AccountRecoveryViewSet, basename='auth-recovery')

urlpatterns = [
    path('api/v1/', include([
        path('', include(api_router.urls)),
        path('me/', MyProfileRetrieveUpdateAPIView.as_view()),
        path('students/', ManagementStudentListView.as_view(), name='management-student-list'),
        path('students/<uuid:pk>/', ManagementStudentDetailView.as_view(), name='management-student-detail'),
        path('teachers/', ManagementTeacherListView.as_view(), name='management-teacher-list'),
        path('teachers/<uuid:pk>/', ManagementTeacherDetailView.as_view(), name='management-teacher-detail'),
        path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
        path("super-admin/students/", SuperAdminStudentListCreateView.as_view()),
        path("super-admin/students/<int:pk>/", SuperAdminStudentDetailView.as_view()),
        path("super-admin/teachers/", SuperAdminTeacherListCreateView.as_view()),
        path("super-admin/teachers/<int:pk>/", SuperAdminTeacherDetailView.as_view()),
        path("super-admin/centers/", SuperAdminCenterListCreateView.as_view()),
        path("super-admin/centers/<uuid:pk>/", SuperAdminCenterDetailView.as_view()),

    ])),
    path('auth/', include([
        path('', include(auth_router.urls)),
        path('login/', LoginAPIView.as_view()),
    ]))
]
