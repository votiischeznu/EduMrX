from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.auth_views import RegisterModelViewSet, AccountRecoveryViewSet, LoginAPIView
from apps.views import MyProfileRetrieveUpdateAPIView, RoomModelViewSet, GroupModelViewSet, GroupStudentModelViewSet

router = SimpleRouter(trailing_slash=False)
router.register('register', RegisterModelViewSet, basename='auth-register')
router.register('recovery', AccountRecoveryViewSet, basename='auth-recovery')
router.register('rooms', RoomModelViewSet, basename='rooms')
router.register('groups', GroupModelViewSet, basename='groups')
router.register('group_students', GroupStudentModelViewSet, basename='group_students')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginAPIView.as_view()),
    path('me/', MyProfileRetrieveUpdateAPIView.as_view()),
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]


