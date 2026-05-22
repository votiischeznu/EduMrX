from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.models import User
from apps.serializers import (
    RecoveryStartSerializer,
    RecoveryVerifySerializer,
    RecoveryCompleteSerializer
)
from apps.redis_otp import AccountRecoveryService


@extend_schema(tags=['Auth'])
class AccountRecoveryViewSet(ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RecoveryStartSerializer,
        responses={200: dict}
    )
    @action(
        detail=False,
        methods=['post'],
        url_path='start'
    )
    def start(self, request):

        serializer = RecoveryStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = User.objects.get(phone=data['phone'])

        result = AccountRecoveryService.start(
            user=user,
            new_phone=data['new_phone'],
            method=data['method']
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=RecoveryVerifySerializer,
        responses={200: dict}
    )
    @action(
        detail=False,
        methods=['post'],
        url_path='verify'
    )
    def verify(self, request):

        serializer = RecoveryVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = User.objects.get(phone=data['phone'])

        result = AccountRecoveryService.verify(
            user=user,
            raw_otp=data['otp']
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        request=RecoveryCompleteSerializer,
        responses={200: dict}
    )
    @action(
        detail=False,
        methods=['post'],
        url_path='complete'
    )
    def complete(self, request):

        serializer = RecoveryCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = User.objects.get(phone=data['phone'])

        AccountRecoveryService.complete(
            user=user,
            new_password=data['new_password']
        )

        return Response(
            {
                "message": "Parol va telefon muvaffaqiyatli yangilandi"
            },
            status=status.HTTP_200_OK
        )