from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.views import (
    RegisterModelViewSet,
    LoginAPIView,
    AccountRecoveryViewSet
)

router = SimpleRouter(trailing_slash=False)
router.register('register', RegisterModelViewSet, basename='auth-register')

router.register('recovery', AccountRecoveryViewSet, basename='auth-recovery')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginAPIView.as_view()),
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]