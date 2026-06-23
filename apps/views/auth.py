from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from apps.models import User
from apps.serializers import (
    LoginModelSerializer,
    RecoveryCompleteSerializer,
    RecoveryStartSerializer,
    RecoveryVerifySerializer,
    RegisterModelSerializer,
)
from apps.serializers.auth import RegisterVerifyOTPSerializer
from apps.serializers.profile import PasswordChangeSerializer
from apps.service.redis_otp import AccountRecoveryService, OTPService

import hashlib
import hmac
import time
from django.conf import settings
from rest_framework import status
from apps.serializers.auth import TelegramOAuthSerializer


@extend_schema(tags=["Auth"])
class PasswordChangeAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user.must_change_password:
            user.must_change_password = False
            user.save()
        update_session_auth_hash(request, user)

        return Response({"message": "Parol muvaffaqiyatli o'zgartirildi"})


@extend_schema(tags=["Auth"])
class RegisterCreateAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterModelSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        phone = data["phone"]
        email = data.get("email", "")
        method = data.get("method", "telegram_bot")

        result = OTPService.start_registration(
            phone=phone, email=email, method=method, registration_data=data
        )
        return Response(result)


@extend_schema(tags=["Auth"])
class RegisterVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterVerifyOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        otp = serializer.validated_data["otp"]
        user = OTPService.complete_registration(phone, otp)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz!",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


@extend_schema(tags=["Auth"])
class LoginAPIView(GenericAPIView):
    serializer_class = LoginModelSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Tizimga muvaffaqiyatli kirdingiz.",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "phone": user.phone,
                    "email": user.email or "",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "must_change_password": user.must_change_password,
                },
            }
        )


@extend_schema(tags=["Auth"])
class AccountRecoveryViewSet(GenericViewSet):
    permission_classes = [AllowAny]

    def _validate_and_get_user(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, phone=serializer.validated_data["phone"])
        return serializer.validated_data, user

    @action(
        detail=False,
        methods=["post"],
        url_path="start",
        serializer_class=RecoveryStartSerializer,
    )
    def start_recovery(self, request):
        data, user = self._validate_and_get_user(request)
        result = AccountRecoveryService.start(
            user=user, new_phone=data["new_phone"], method=data["method"]
        )
        return Response(result)

    @action(
        detail=False,
        methods=["post"],
        url_path="verify",
        serializer_class=RecoveryVerifySerializer,
    )
    def verify_recovery(self, request):
        data, user = self._validate_and_get_user(request)
        result = AccountRecoveryService.verify(user=user, raw_otp=data["otp"])
        return Response(result)

    @action(
        detail=False,
        methods=["post"],
        url_path="complete",
        serializer_class=RecoveryCompleteSerializer,
    )
    def complete_recovery(self, request):
        data, user = self._validate_and_get_user(request)
        AccountRecoveryService.complete(user=user, new_password=data["new_password"])
        return Response({"message": "Parol va telefon muvaffaqiyatli yangilandi"})

# apps/views/auth.py (qo'shimcha)



class TelegramOAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TelegramOAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.save()
        return Response(tokens, status=status.HTTP_200_OK)
