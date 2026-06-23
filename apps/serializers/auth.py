import re
from datetime import timedelta

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, EmailField
from rest_framework.serializers import ModelSerializer, Serializer
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.models import User
from apps.utils.phone import normalize_phone
import hashlib
import hmac
import time
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

PHONE_REGEX = r"^\998\d{9}$"


def validate_uzbek_phone(value: str):
    normalized = normalize_phone(value)
    if not re.match(r"^998\d{9}$", normalized):
        raise ValidationError("Telefon format noto'g'ri. Masalan: +998901234567")
    return normalized


class RegisterModelSerializer(ModelSerializer):
    phone = CharField(max_length=30, validators=[validate_uzbek_phone])
    email = EmailField(required=False, allow_blank=True)
    method = ChoiceField(choices=["email", "telegram_bot"], default="telegram_bot")
    password = CharField(write_only=True)
    confirm_password = CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "email",
            "method",
            "first_name",
            "last_name",
            "password",
            "confirm_password",
        )
        extra_kwargs = {"id": {"read_only": True}, "password": {"write_only": True}}

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        user = User.objects.filter(phone=normalized).first()
        if user:
            six_months_ago = timezone.now() - timedelta(days=180)
            if not user.is_active and user.updated_at < six_months_ago:
                user.phone = f"{user.phone}_{user.id.hex[:5]}"
                user.save(update_fields=["phone"])
                return value
            raise ValidationError("Bu telefon raqam allaqachon mavjud va faol holatda.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise ValidationError({"confirm_password": "Parollar mos emas"})

        try:
            validate_password(attrs["password"])
        except DjangoValidationError as e:
            raise ValidationError({"password": list(e.messages)})

        method = attrs.get("method", "telegram_bot")
        email = attrs.get("email")
        if method == "email" and not email:
            raise ValidationError({"email": "Email orqali tasdiqlash uchun email manzilini kiritish majburiy."})

        return attrs

    def create(self, validated_data):

        return validated_data


class RegisterVerifyOTPSerializer(Serializer):
    phone = CharField(max_length=30, validators=[validate_uzbek_phone])
    otp = CharField(max_length=4, min_length=4)


class LoginModelSerializer(Serializer):
    phone = CharField(max_length=30, validators=[validate_uzbek_phone])
    password = CharField(write_only=True)

    def validate(self, attrs):
        raw_phone = attrs.get("phone", "")
        password = attrs.get("password")

        normalized = re.sub(r"[\s\-\(\)]", "", raw_phone).lstrip("+")

        user = User.objects.filter(phone=normalized).first() or User.objects.filter(phone="+" + normalized).first()
        if not user or not user.check_password(password):
            raise ValidationError("Telefon raqam yoki parol xato.")

        if not user.is_active:
            raise ValidationError("Foydalanuvchi faol emas. Profilingiz bloklangan!")

        expected_role = self.context.get("expected_role")
        if expected_role and user.role != expected_role:
            raise ValidationError("Siz bu paneliga kira olmaysiz.")

        attrs["user"] = user
        return attrs


class RecoveryStartSerializer(Serializer):
    phone = CharField(max_length=30, validators=[validate_uzbek_phone])
    new_phone = CharField(max_length=30, validators=[validate_uzbek_phone])
    method = ChoiceField(
        choices=[("email", "Email"), ("telegram_bot", "Telegram Bot")],
        default="telegram_bot",
    )

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        user = User.objects.filter(phone=normalized).first()
        if not user:
            raise ValidationError("Ushbu telefon raqamli foydalanuvchi topilmadi")

        if not user.is_active:
            raise ValidationError("Ushbu foydalanuvchi faol emas, parolni tiklab bo'lmaydi")
        return value

    def validate_new_phone(self, value):
        normalized = normalize_phone(value)
        user = User.objects.filter(phone=normalized).first()
        if user:
            six_months_ago = timezone.now() - timedelta(days=180)
            if not user.is_active and user.updated_at < six_months_ago:
                user.phone = f"{user.phone}_{user.id.hex[:5]}"
                user.save(update_fields=["phone"])
                return value

            raise ValidationError("Bu yangi telefon raqam allaqachon boshqa foydalanuvchi tomonidan band qilingan")
        return value


class RecoveryVerifySerializer(Serializer):
    phone = CharField(max_length=30, validators=[validate_uzbek_phone])
    otp = CharField(max_length=6)

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        user = User.objects.filter(phone=normalized).first()
        if not user or not user.is_active:
            raise ValidationError("Ushbu telefon raqamli faol foydalanuvchi topilmadi")
        return value


class RecoveryCompleteSerializer(Serializer):
    phone = CharField(max_length=30, validators=[validate_uzbek_phone])
    new_password = CharField(write_only=True)

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        user = User.objects.filter(phone=normalized).first()
        if not user or not user.is_active:
            raise ValidationError("Ushbu telefon raqamli faol foydalanuvchi topilmadi")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value




def verify_telegram_hash(data: dict, bot_token: str) -> bool:
    """
    Telegram OAuth hash tekshiruvi.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    received_hash = data.get("hash")
    if not received_hash:
        return False

    # hash ni olib tashlaymiz, qolganlarni tekshiramiz
    check_dict = {k: v for k, v in data.items() if k != "hash" and v is not None}

    # data-check-string: key=value satrlarni \n bilan birlashtir (alifbo tartibida)
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(check_dict.items()))

    # secret_key = SHA-256(bot_token)
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # HMAC-SHA-256
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_hash, received_hash)


class TelegramOAuthSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    username = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    photo_url = serializers.URLField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    auth_date = serializers.IntegerField()
    hash = serializers.CharField(max_length=128)

    def validate(self, attrs):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not bot_token:
            raise serializers.ValidationError("TELEGRAM_BOT_TOKEN sozlanmagan.")

        # 1. Hash tekshiruvi
        raw_data = self.initial_data  # original dict (barcha fieldlar bilan)
        if not verify_telegram_hash(raw_data, bot_token):
            raise serializers.ValidationError("Telegram hash noto'g'ri. Autentifikatsiya rad etildi.")

        # 2. auth_date eski emas (5 daqiqadan ko'p bo'lmasin)
        max_age = getattr(settings, "TELEGRAM_AUTH_MAX_AGE", 300)  # sekund
        now = int(time.time())
        if now - attrs["auth_date"] > max_age:
            raise serializers.ValidationError("Telegram auth_date eskirgan.")

        return attrs

    def save(self, **kwargs):
        data = self.validated_data
        telegram_id = data["id"]
        phone = data.get("phone", "").strip()

        # telegram_id bo'yicha topamiz
        user = User.objects.filter(telegram_id=telegram_id).first()

        if user is None and phone:
            # Telefon bo'yicha ham qidiramiz (avval ro'yxatdan o'tgan bo'lishi mumkin)
            from apps.utils import normalize_phone  # mavjud utility

            normalized = normalize_phone(phone)
            user = User.objects.filter(phone=normalized).first()
            if user is None:
                user = User.objects.filter(phone=f"+{normalized}").first()

        if user is None:
            # Yangi user yaratamiz
            user = self._create_user(data, phone)
        else:
            # Mavjud userni yangilaymiz
            self._update_user(user, data, phone)

        # JWT token generatsiya
        refresh = RefreshToken.for_user(user)

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": str(user.id),
                "full_name": user.get_full_name(),
                "phone": user.phone or "",
                "role": user.role,
                "telegram_id": user.telegram_id,
            },
        }

    def _create_user(self, data: dict, phone: str) -> User:


        first_name = data["first_name"]
        last_name = data.get("last_name", "")
        telegram_id = data["id"]

        # Phone normalizatsiya
        normalized_phone = None
        if phone:
            raw = normalize_phone(phone)
            normalized_phone = f"+{raw}"

        user = User(
            first_name=first_name,
            last_name=last_name,
            telegram_id=telegram_id,
            role=User.Role.STUDENT,  # default role — kerak bo'lsa o'zgartiring
            is_active=True,
        )

        if normalized_phone:
            user.phone = normalized_phone
        else:
            # Phone yo'q — Telegram ID asosida placeholder
            user.phone = f"tg_{telegram_id}"

        user.set_unusable_password()
        user.save()
        return user

    def _update_user(self, user: User, data: dict, phone: str) -> None:
        from apps.utils import normalize_phone

        changed = False

        # telegram_id yangilaymiz (telefon orqali topilgan bo'lsa)
        if not user.telegram_id:
            user.telegram_id = data["id"]
            changed = True

        # Telefon yangilaymiz (OAuth yangi telefon yuborgan bo'lsa)
        if phone:
            raw = normalize_phone(phone)
            normalized_phone = f"+{raw}"
            if user.phone != normalized_phone:
                user.phone = normalized_phone
                changed = True

        if changed:
            user.save(update_fields=["telegram_id", "phone"] if phone else ["telegram_id"])
