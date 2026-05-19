from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.models import User
from apps.serializer import UserModelSerializer, RegisterModelSerializer, LoginModelSerializer


@extend_schema(tags=['User'])
class UserModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'patch', 'delete']


@extend_schema(tags=['Register'])
class RegisterModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterModelSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post']


@extend_schema(tags=['Login'])
class LoginAPIView(APIView):

    def post(self, request):
        serializer = LoginModelSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            'message': 'Login Successful',
            'user_id': user.id,
        }, status=status.HTTP_200_OK)
