# apps/service/redis_otp.py
import collections.abc

if not hasattr(collections, "MutableMapping"):
    collections.MutableMapping = collections.abc.MutableMapping

import hashlib
import json
import logging
import os
import random
import uuid

import fakeredis
import redis
from django.conf import settings as django_settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.models import User

try:
    if os.getenv("REDIS_URL"):
        r = redis.Redis.from_url(django_settings.REDIS_URL, decode_responses=True)
    else:
        r = fakeredis.FakeRedis(decode_responses=True)
except Exception:
    r = fakeredis.FakeRedis(decode_responses=True)

OTP_TTL = 300
MAX_ATTEMPTS = 5
BOT_USERNAME = "edu_verify_system_bot"
logger = logging.getLogger(__name__)


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


class OTPService:
    @staticmethod
    def _key(identifier: str):
        return f"otp_verification:{identifier}"

    @staticmethod
    def _bot_token_key(token: str):
        return f"bot_token:{token}"

    @staticmethod
    def start_registration(phone: str, email: str, method: str, registration_data: dict):
        otp_code = str(random.randint(1000, 9999))
        hashed_otp = _hash_otp(otp_code)
        payload = {
            "otp": hashed_otp,
            "phone": phone,
            "email": email,
            "first_name": registration_data.get("first_name", ""),
            "last_name": registration_data.get("last_name", ""),
            "password": registration_data.get("password"),
            "method": method,
            "attempts": 0,
            "purpose": "registration",
            # Telegram orqali tanlangan bo'lsa, bot /start bosilganda
            # shu ikki maydon to'ldiriladi (run_bot.py ga qarang).
            "telegram_chat_id": None,
            "telegram_username": "",
        }

        r.setex(OTPService._key(phone), OTP_TTL, json.dumps(payload))

        if method == "telegram_bot":
            link_token = f"reg_{uuid.uuid4().hex[:16]}"
            bot_payload = {"phone": phone, "email": email}
            r.setex(OTPService._bot_token_key(link_token), OTP_TTL, json.dumps(bot_payload))

            return {
                "message": "Iltimos, Telegram botimizga o'ting va akkauntni faollashtirish uchun START tugmasini bosing.",
                "step": "awaiting_bot_start",
                "bot_link": f"https://t.me/{BOT_USERNAME}?start={link_token}",
            }

        elif method == "email":
            try:
                send_mail(
                    subject="EduPlatform - Ro'yxatdan o'tish",
                    message=f"Sizning ro'yxatdan o'tish uchun tasdiqlash kodingiz: {otp_code}\nUshbu kod 5 daqiqa davomida faol.",
                    from_email=django_settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                r.delete(OTPService._key(phone))
                logger.error(f"Email yuborishda xatolik: {str(e)}")
                raise ValidationError("Emailga kod yuborishda xatolik yuz berdi.")

            response = {
                "message": "Emailingizga tasdiqlash kodi yuborildi.",
                "step": "awaiting_otp_verify",
            }
            if django_settings.DEBUG:
                response["otp_for_dev"] = otp_code
            return response

    @staticmethod
    def complete_registration(phone: str, raw_otp: str):
        key = OTPService._key(phone)
        raw = r.get(key)
        if not raw:
            raise ValidationError("Tasdiqlash muddati tugagan yoki noto'g'ri seans.")

        data = json.loads(raw)

        if data.get("attempts", 0) >= MAX_ATTEMPTS:
            r.delete(key)
            raise ValidationError("Urinishlar soni tugadi. Qaytadan ro'yxatdan o'ting.")

        if data["otp"] != _hash_otp(raw_otp):
            data["attempts"] = data.get("attempts", 0) + 1
            r.setex(key, OTP_TTL, json.dumps(data))
            raise ValidationError("Tasdiqlash kodi noto'g'ri.")

        user = User.objects.create_user(
            phone=data["phone"],
            email=data.get("email"),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            password=data["password"],
        )
        user.is_active = True

        # ── Telegram orqali ro'yxatdan o'tgan bo'lsa, telegram_id ni
        # shu yerda birga saqlaymiz — foydalanuvchi profilidan alohida
        # "ulash" qilishiga hojat qolmaydi.
        telegram_chat_id = data.get("telegram_chat_id")
        if telegram_chat_id:
            already_taken = User.objects.filter(telegram_id=telegram_chat_id).exclude(id=user.id).exists()
            if not already_taken:
                user.telegram_id = telegram_chat_id
                user.telegram_username = data.get("telegram_username", "")
                user.telegram_linked_at = timezone.now()
            else:
                logger.warning(
                    "Telegram chat_id=%s allaqachon boshqa userga bog'langan, user_id=%s uchun bog'lanmadi.",
                    telegram_chat_id,
                    user.id,
                )

        user.save()

        r.delete(key)
        return user


class AccountRecoveryService:
    @staticmethod
    def start(user: User, new_phone: str, method: str):
        otp_code = str(random.randint(100000, 999999))
        payload = {
            "otp": _hash_otp(otp_code),
            "new_phone": new_phone,
            "method": method,
            "verified": False,
            "attempts": 0,
            "purpose": "recovery",
        }

        r.setex(OTPService._key(str(user.id)), OTP_TTL, json.dumps(payload))

        if method == "telegram_bot":
            link_token = f"rec_{uuid.uuid4().hex[:16]}"
            bot_payload = {"user_id": str(user.id), "new_phone": new_phone}
            r.setex(OTPService._bot_token_key(link_token), OTP_TTL, json.dumps(bot_payload))

            return {
                "message": "Parolni tiklash uchun botimizga o'ting va START tugmasini bosing.",
                "step": "awaiting_bot_start",
                "bot_link": f"https://t.me/{BOT_USERNAME}?start={link_token}",
            }

        elif method == "email":
            if not user.email:
                raise ValidationError("Ushbu foydalanuvchining hisobiga email bog'lanmagan. Bot orqali tiklang.")
            try:
                send_mail(
                    subject="Akkauntni tiklash tasdiqlash kodi",
                    message=f"Sizning parolni tiklash uchun tasdiqlash kodingiz: {otp_code}",
                    from_email=django_settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                r.delete(OTPService._key(str(user.id)))
                raise ValidationError("Emailga kod yuborishda xatolik yuz berdi.")

            response = {
                "message": "Emailingizga tasdiqlash kodi yuborildi.",
                "step": "awaiting_otp_verify",
            }
            if django_settings.DEBUG:
                response["otp_for_dev"] = otp_code
            return response

    @staticmethod
    def verify(user: User, raw_otp: str):
        key = OTPService._key(str(user.id))
        raw = r.get(key)
        if not raw:
            raise ValidationError("Muddati tugagan seans.")

        data = json.loads(raw)
        if data.get("attempts", 0) >= MAX_ATTEMPTS:
            r.delete(key)
            raise ValidationError("Urinishlar soni tugadi.")

        if data["otp"] != _hash_otp(raw_otp):
            data["attempts"] = data.get("attempts", 0) + 1
            r.setex(key, OTP_TTL, json.dumps(data))
            raise ValidationError("Kod noto'g'ri.")

        data["verified"] = True
        r.setex(key, OTP_TTL, json.dumps(data))
        return {"message": "Kod muvaffaqiyatli tasdiqlandi"}

    @staticmethod
    def complete(user: User, new_password: str) -> User:
        key = OTPService._key(str(user.id))
        raw = r.get(key)
        if not raw:
            raise ValidationError("Tiklash seansi topilmadi.")

        data = json.loads(raw)
        if not data.get("verified"):
            raise ValidationError("Kod hali tasdiqlanmagan.")

        user.set_password(new_password)
        if data.get("new_phone"):
            user.phone = data["new_phone"]
        user.save()
        r.delete(key)
        return user
