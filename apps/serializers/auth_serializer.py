from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models import User


class RegisterModelSerializer(ModelSerializer):
    password = CharField(write_only=True)
    confirm_password = CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'email', 'first_name', 'last_name', 'password', 'confirm_password',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.pop('confirm_password', None):
            raise ValidationError({
                'confirm_password': "Parollar mos emas"
            })
        return attrs

    def validate_phone(self, value):
        if not value.startswith('+998'):
            raise ValidationError("Telefon +998 bilan boshlanishi kerak")

        if not value[1:].isdigit():
            raise ValidationError("Telefon raqamingiz faqat raqamlardan iborat bulishi kerak")

        if len(value) != 13:
            raise ValidationError("Telefon raqam noto‘g‘ri")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        return User.objects.create_user(**validated_data)


class LoginModelSerializer(Serializer):
    phone = CharField()
    password = CharField(write_only=True)

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            phone=phone,
            password=password
        )

        if not user:
            raise ValidationError("Telefon raqam yoki parol xato")

        if not user.is_active:
            raise ValidationError("Foydalanuvchi aktiv emas")

        attrs['user'] = user
        return attrs


class RecoveryStartSerializer(Serializer):
    phone = CharField(max_length=13)
    new_phone = CharField(max_length=13)
    method = CharField()

    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise ValidationError("Ushbu telefon raqamli foydalanuvchi topilmadi")
        return value

    def validate_new_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise ValidationError("Ushbu telefon raqam allaqachon mavjud")
        return value


class RecoveryVerifySerializer(Serializer):
    phone = CharField(max_length=13)
    otp = CharField(max_length=6)

    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise ValidationError("Ushbu  telefon raqamli foydalanuvchi topilmadi")
        return value



class RecoveryCompleteSerializer(Serializer):
    phone = CharField(max_length=13)
    new_password = CharField(min_length=8, write_only=True)

    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise ValidationError("Ushbu  telefon raqamli foydalanuvchi topilmadi")
        return value