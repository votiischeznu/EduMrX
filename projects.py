from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.models import User
from apps.redis_otp import AccountRecoveryService, RegisterVerificationService
from apps.serializers import (
    LoginModelSerializer, RegisterStartSerializer, RegisterVerifySerializer,
    RecoveryVerifySerializer, RecoveryCompleteSerializer, RecoveryStartSerializer
)
from apps.serializers.profile_serializers import PasswordChangeSerializer


@extend_schema(tags=['Auth'])
class PasswordChangeApiView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request, user)
        return Response({'message': 'Parol muvaffaqiyatli uzgartirildi'})


@extend_schema(tags=['Auth'])
class RegisterViewSet(GenericViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='register-start', serializer_class=RegisterStartSerializer)
    def register_start(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = RegisterVerificationService.start_registration(serializer.validated_data)
        return Response(result)

    @action(detail=False, methods=['post'], url_path='register-verify', serializer_class=RegisterVerifySerializer)
    def register_verify(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        result = RegisterVerificationService.verify_registration(phone=data['phone'], raw_otp=data['otp'])
        return Response(result)


@extend_schema(tags=['Auth'])
class LoginAPIView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = LoginModelSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            'message': 'Login Successful',
            'user_id': user.id,
        })


@extend_schema(tags=['Auth'])
class AccountRecoveryViewSet(GenericViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='recovery-start', serializer_class=RecoveryStartSerializer)
    def start_recovery(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_object_or_404(User, phone=data['phone'])

        result = AccountRecoveryService.start(user=user, new_phone=data['new_phone'], method=data['method'])
        return Response(result)

    @action(detail=False, methods=['post'], url_path='recovery-verify', serializer_class=RecoveryVerifySerializer)
    def verify_recovery(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_object_or_404(User, phone=data['phone'])

        result = AccountRecoveryService.verify(user=user, raw_otp=data['otp'])
        return Response(result)

    @action(detail=False, methods=['post'], url_path='recovery-complete', serializer_class=RecoveryCompleteSerializer)
    def complete_recovery(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_object_or_404(User, phone=data['phone'])

        AccountRecoveryService.complete(user=user, new_password=data['new_password'])
        return Response({"message": "Parol va telefon muvaffaqiyatli yangilandi"})