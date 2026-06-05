import re
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, EmailField
from rest_framework.serializers import ModelSerializer, Serializer
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.models import User

PHONE_REGEX = r'^\+998\d{9}$'


def validate_uzbek_phone(value: str):
    if not re.match(PHONE_REGEX, value):
        raise ValidationError("Telefon format noto‘g‘ri. Masalan: +998901234567")
    return value


class RegisterModelSerializer(ModelSerializer):
    phone = CharField(max_length=13, validators=[validate_uzbek_phone])
    email = EmailField(required=False, allow_blank=True)
    method = ChoiceField(choices=['email', 'telegram_bot'], default='telegram_bot')
    password = CharField(write_only=True)
    confirm_password = CharField(write_only=True)

    class Meta:
        model = User
        fields = 'id', 'phone', 'email', 'method', 'first_name', 'last_name', 'password', 'confirm_password'
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True}
        }

    def validate_phone(self, value):
        user = User.objects.filter(phone=value).first()
        if user:
            six_months_ago = timezone.now() - timedelta(days=180)
            if not user.is_active and user.updated_at < six_months_ago:
                user.phone = f"{user.phone}_{user.id.hex[:5]}"
                user.save(update_fields=['phone'])
                return value
            raise ValidationError("Bu telefon raqam allaqachon mavjud va faol holatda.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            raise ValidationError({'confirm_password': "Parollar mos emas"})

        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise ValidationError({"password": list(e.messages)})

        method = attrs.get('method', 'telegram_bot')
        email = attrs.get('email')
        if method == 'email' and not email:
            raise ValidationError({"email": "Email orqali tasdiqlash uchun email manzilini kiritish majburiy."})

        return attrs

    def create(self, validated_data):

        return validated_data


class RegisterVerifyOTPSerializer(Serializer):
    phone = CharField(max_length=13, validators=[validate_uzbek_phone])
    otp = CharField(max_length=4, min_length=4)


class LoginModelSerializer(Serializer):
    phone = CharField(max_length=13, validators=[validate_uzbek_phone])
    password = CharField(write_only=True)

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')

        authenticated_user = authenticate(
            request=self.context.get('request'),
            username=phone,
            password=password
        )
        if not authenticated_user:
            raise ValidationError("Telefon raqam yoki parol xato.")

        if not authenticated_user.is_active:
            raise ValidationError("Foydalanuvchi faol emas. Profilingiz bloklangan!")

        attrs['user'] = authenticated_user
        return attrs

class RecoveryStartSerializer(Serializer):
    phone = CharField(max_length=13, validators=[validate_uzbek_phone])
    new_phone = CharField(max_length=13, validators=[validate_uzbek_phone])
    method = ChoiceField(
        choices=[
            ('email', 'Email'),
            ('telegram_bot', 'Telegram Bot')
        ], default='telegram_bot')

    def validate_phone(self, value):
        user = User.objects.filter(phone=value).first()
        if not user:
            raise ValidationError("Ushbu telefon raqamli foydalanuvchi topilmadi")

        if not user.is_active:
            raise ValidationError("Ushbu foydalanuvchi faol emas, parolni tiklab bo'lmaydi")
        return value

    def validate_new_phone(self, value):
        user = User.objects.filter(phone=value).first()
        if user:
            six_months_ago = timezone.now() - timedelta(days=180)
            if not user.is_active and user.updated_at < six_months_ago:
                user.phone = f"{user.phone}_{user.id.hex[:5]}"
                user.save(update_fields=['phone'])
                return value

            raise ValidationError("Bu yangi telefon raqam allaqachon boshqa foydalanuvchi tomonidan band qilingan")
        return value


class RecoveryVerifySerializer(Serializer):
    phone = CharField(max_length=13, validators=[validate_uzbek_phone])
    otp = CharField(max_length=6)

    def validate_phone(self, value):
        user = User.objects.filter(phone=value).first()
        if not user or not user.is_active:
            raise ValidationError("Ushbu telefon raqamli faol foydalanuvchi topilmadi")
        return value


class RecoveryCompleteSerializer(Serializer):
    phone = CharField(max_length=13, validators=[validate_uzbek_phone])
    new_password = CharField(write_only=True)

    def validate_phone(self, value):
        user = User.objects.filter(phone=value).first()
        if not user or not user.is_active:
            raise ValidationError("Ushbu telefon raqamli faol foydalanuvchi topilmadi")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value
