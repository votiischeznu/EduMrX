from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from apps.models import User
from apps.serializer import UserModelSerializer, RegisterModelSerializer


@extend_schema(tags=['User'])
class UserModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get','post', 'patch', 'delete']


@extend_schema(tags=['Register'])
class RegisterModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterModelSerializer
    http_method_names = ['get','post']