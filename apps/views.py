from django.contrib.auth import update_session_auth_hash
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from apps.models import User
from apps.redis_otp import AccountRecoveryService
from apps.serializers import StudentProfileSerializer, TeacherProfileSerializer, AdminProfileSerializer, \
    LoginModelSerializer, RegisterModelSerializer, RecoveryVerifySerializer, RecoveryCompleteSerializer, \
    RecoveryStartSerializer
from apps.serializers.profile_serializers import PasswordChangeSerializer


@extend_schema(tags=['Profile'])
class MyProfileRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', ]

    def get_serializer_class(self):
        role = self.request.user.role

        if role == User.Role.STUDENT:
            return StudentProfileSerializer

        elif role == User.Role.TEACHER:
            return TeacherProfileSerializer

        return AdminProfileSerializer

    def get_object(self):
        return self.request.user


@extend_schema(tags=['Auth'])
class PasswordChangeApiView(GenericAPIView):
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

        return Response({
            'message': 'Parol muvaffaqiyatli uzgartirildi',
        })


@extend_schema(tags=['Auth'])
class RegisterModelViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterModelSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']


@extend_schema(tags=['Auth'])
class LoginAPIView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = LoginModelSerializer
    permission_classes = [AllowAny]

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
        return Response(result)

    @extend_schema(request=RecoveryVerifySerializer, responses={200: dict})
    @action(detail=False, methods=['post'], url_path='recovery-verify')
    def verify_recovery(self, request):
        serializer = RecoveryVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = User.objects.get(phone=data['phone'])

        result = AccountRecoveryService.verify(user=user, raw_otp=data['otp'])
        return Response(result)

    @extend_schema(request=RecoveryCompleteSerializer, responses={200: dict})
    @action(detail=False, methods=['post'], url_path='recovery-complete')
    def complete_recovery(self, request):
        serializer = RecoveryCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = User.objects.get(phone=data['phone'])

        AccountRecoveryService.complete(user=user, new_password=data['new_password'])
        return Response({"message": "Parol va telefon muvaffaqiyatli yangilandi"})
