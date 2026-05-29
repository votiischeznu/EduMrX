# apps/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.views import MyProfileRetrieveUpdateAPIView, RoomModelViewSet, GroupModelViewSet, GroupStudentModelViewSet, \
    RegisterModelViewSet, AccountRecoveryViewSet, LoginAPIView

api_router = SimpleRouter(trailing_slash=False)
api_router.register('rooms', RoomModelViewSet, basename='rooms')
api_router.register('groups', GroupModelViewSet, basename='groups')
api_router.register('group_students', GroupStudentModelViewSet, basename='group_students')
auth_router = SimpleRouter(trailing_slash=False)
auth_router.register('register', RegisterModelViewSet, basename='auth-register')
auth_router.register('recovery', AccountRecoveryViewSet, basename='auth-recovery')

urlpatterns = [
    path('api/v1/', include([
        path('', include(api_router.urls)),
        path('me/', MyProfileRetrieveUpdateAPIView.as_view()),
        path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    ])),
    path('auth/', include(auth_router.urls)),
    path('auth/login/', LoginAPIView.as_view()),
]