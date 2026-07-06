# apps/serializers/auth.py
import hashlib
import hmac
import re
import time

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, EmailField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.models import User
from apps.utils.phone import normalize_phone

PHONE_REGEX = r"^\998\d{9}$"

# Telegram Login Widget faqat shu maydonlarni yuboradi.
# Boshqa maydonlar (frontend xato qo'shib yuborgan bo'lsa ham) hash
# hisobiga kiritilmaydi — aks holda hash doim mos kelmaydi.

TELEGRAM_AUTH_FIELDS = {"id", "phone", "first_name", "last_name", "username", "photo_url", "auth_date"}


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
        # User.objects endi default holda is_deleted=False bo'lganlarni
        # qaytaradi (apps/models/manager.py), shuning uchun bu yerda
        # o'chirilgan/eski userlar bilan qo'lda ishlashning hojati yo'q —
        # agar topilsa, demak u haqiqatan ham faol va band.
        if User.objects.filter(phone=normalized).exists():
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

        # User.objects endi is_deleted=True bo'lganlarni umuman qaytarmaydi,
        # shuning uchun o'chirilgan user bu yerda "topilmadi" deb chiqadi —
        # xavfsizlik nuqtai nazaridan to'g'ri (aniq sabab oshkor qilinmaydi).
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
        # is_deleted=True bo'lgan eski userlar User.objects orqali umuman
        # ko'rinmaydi (va ularning telefoni soft_delete() paytida allaqachon
        # bo'shatilgan), shuning uchun bu yerda topilgan har qanday user —
        # haqiqatan ham faol va raqam band.
        if User.objects.filter(phone=normalized).exists():
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
    Telegram Login Widget hash tekshiruvi.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    received_hash = data.get("hash")
    if not received_hash:
        return False

    check_dict = {k: v for k, v in data.items() if k in TELEGRAM_AUTH_FIELDS and v is not None and v != ""}

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(check_dict.items()))

    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_hash, received_hash)


class TelegramOAuthSerializer(serializers.Serializer):
    """
    Telegram Login Widget orqali login.
    DIQQAT: bu faqat 'tan olish' (foydalanuvchini telegram_id orqali
    topish) uchun ishlatiladi — bu yerda yangi user YARATILMAYDI.
    Chunki sizning tizimingizda har bir user (Parent/Student/Teacher/
    Manager/Director/SuperAdmin) avval registratsiya orqali (telefon +
    parol bilan) yaratiladi, telegram_id esa keyin (registratsiya
    paytida avtomatik yoki profildan qo'lda) bog'lanadi.

    Agar telegram_id bo'yicha user topilmasa, bu "hali bog'lanmagan"
    degani — login rad etiladi va foydalanuvchiga aniq xabar beriladi.
    """

    id = serializers.IntegerField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    username = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    photo_url = serializers.URLField(required=False, allow_blank=True, default="")
    auth_date = serializers.IntegerField()
    hash = serializers.CharField(max_length=128)

    def validate(self, attrs):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not bot_token:
            raise serializers.ValidationError("TELEGRAM_BOT_TOKEN sozlanmagan.")

        raw_data = self.initial_data
        if not verify_telegram_hash(raw_data, bot_token):
            raise serializers.ValidationError("Telegram hash noto'g'ri. Autentifikatsiya rad etildi.")

        max_age = getattr(settings, "TELEGRAM_AUTH_MAX_AGE", 300)
        now = int(time.time())
        if now - attrs["auth_date"] > max_age:
            raise serializers.ValidationError("Telegram auth_date eskirgan. Qaytadan urinib ko'ring.")

        # User.objects is_deleted=True bo'lgan userni umuman qaytarmaydi.
        user = User.objects.filter(telegram_id=attrs["id"]).first()
        if not user:
            raise serializers.ValidationError(
                "Bu Telegram akkaunt hech qaysi foydalanuvchiga bog'lanmagan. "
                "Avval ro'yxatdan o'ting yoki profilingizdan Telegramni ulang."
            )

        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi faol emas.")

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        data = self.validated_data

        # Username o'zgargan bo'lsa yangilaymiz (ixtiyoriy, lekin foydali)
        username = data.get("username", "")
        if username and user.telegram_username != username:
            user.telegram_username = username
            user.save(update_fields=["telegram_username"])

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