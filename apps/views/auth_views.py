from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from apps.models import User
from apps.redis_otp import AccountRecoveryService
from apps.serializers import LoginModelSerializer, RecoveryCompleteSerializer, RecoveryStartSerializer, \
    RecoveryVerifySerializer, RegisterModelSerializer
from apps.serializers.profile_serializers import PasswordChangeSerializer


@extend_schema(tags=['Auth'])
class PasswordChangeAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request, user)

        return Response({'message': 'Parol muvaffaqiyatli o‘zgartirildi'})


@extend_schema(tags=['Auth'])
class RegisterModelViewSet(CreateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterModelSerializer
    permission_classes = [AllowAny]


@extend_schema(tags=['Auth'])
class LoginAPIView(GenericAPIView):
    serializer_class = LoginModelSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'phone': user.phone,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })


@extend_schema(tags=['Auth'])
class AccountRecoveryViewSet(GenericViewSet):
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'start_recovery':
            return RecoveryStartSerializer
        elif self.action == 'verify_recovery':
            return RecoveryVerifySerializer
        return RecoveryCompleteSerializer

    def _get_user_from_data(self, serializer):
        return get_object_or_404(User, phone=serializer.validated_data['phone'])

    @action(detail=False, methods=['post'], url_path='recovery-start')
    def start_recovery(self, request):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = self._get_user_from_data(serializer)

        result = AccountRecoveryService.start(
            user=user,
            new_phone=data['new_phone'],
            method=data['method'])
        return Response(result)

    @action(detail=False, methods=['post'], url_path='recovery-verify')
    def verify_recovery(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = self._get_user_from_data(serializer)
        
        result = AccountRecoveryService.verify(user=user, raw_otp=data['otp'])
        return Response(result)

    @action(detail=False, methods=['post'], url_path='recovery-complete')
    def complete_recovery(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = self._get_user_from_data(serializer)

        AccountRecoveryService.complete(user=user, new_password=data['new_password'])

        return Response({'message': 'Parol va telefon muvaffaqiyatli yangilandi'})
