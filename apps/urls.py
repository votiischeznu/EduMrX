from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.views import UserModelViewSet, RegisterModelViewSet

router = SimpleRouter(trailing_slash=False)
router.register('users', UserModelViewSet)
router.register('register', RegisterModelViewSet, basename='auth-register')


urlpatterns = [
    path('', include(router.urls)),
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]
