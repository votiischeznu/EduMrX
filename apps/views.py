from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from apps.models import User
from apps.redis_otp import AccountRecoveryService
from apps.serializers.auth_serializer import (
    RegisterModelSerializer,
    LoginModelSerializer,
    RecoveryStartSerializer,
    RecoveryVerifySerializer,
    RecoveryCompleteSerializer
)



@extend_schema(tags=['Auth'])
class RegisterModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterModelSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post']


@extend_schema(tags=['Auth'])
class LoginAPIView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = LoginModelSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            'message': 'Login Successful',
            'user_id': user.id,
        })


@extend_schema(tags=['Auth'])
class AccountRecoveryViewSet(ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(request=RecoveryStartSerializer, responses={200: dict})
    @action(detail=False, methods=['post'], url_path='recovery-start')
    def start_recovery(self, request):
        serializer = RecoveryStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = User.objects.get(phone=data['phone'])

        result = AccountRecoveryService.start(
            user=user,
            new_phone=data['new_phone'],
            method=data['method']
        )
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(request=RecoveryVerifySerializer, responses={200: dict})
    @action(detail=False, methods=['post'], url_path='recovery-verify')
    def verify_recovery(self, request):
        serializer = RecoveryVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = User.objects.get(phone=data['phone'])

        result = AccountRecoveryService.verify(user=user, raw_otp=data['otp'])
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(request=RecoveryCompleteSerializer, responses={200: dict})
    @action(detail=False, methods=['post'], url_path='recovery-complete')
    def complete_recovery(self, request):
        serializer = RecoveryCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = User.objects.get(phone=data['phone'])

        AccountRecoveryService.complete(user=user, new_password=data['new_password'])
        return Response({"message": "Parol va telefon muvaffaqiyatli yangilandi"}, status=status.HTTP_200_OK)