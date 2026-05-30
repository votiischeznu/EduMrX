import collections.abc

if not hasattr(collections, 'MutableMapping'):
    collections.MutableMapping = collections.abc.MutableMapping

import hashlib
import json
import logging
import random
import uuid
import redis
from django.conf import settings as django_settings
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from apps.models import User

import os
import fakeredis

try:
    if os.getenv('REDIS_URL'):
        r = redis.Redis.from_url(django_settings.REDIS_URL, decode_responses=True)
    else:
        r = fakeredis.FakeRedis(decode_responses=True)
except Exception:
    r = fakeredis.FakeRedis(decode_responses=True)

OTP_TTL = 60 * 5
MAX_ATTEMPTS = 5
BOT_USERNAME = "edu_verify_system_bot"
logger = logging.getLogger(__name__)


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


class OTPService:
    @staticmethod
    def _key(user_id: str):
        return f"otp_verification:{user_id}"

    @staticmethod
    def _get_data(user_id: str):
        raw = r.get(OTPService._key(user_id))
        if not raw:
            raise ValidationError("Kod muddati o'tgan yoki mavjud emas")
        return json.loads(raw)

    @staticmethod
    def verify(user_id: str, raw_otp: str):
        key = OTPService._key(user_id)
        data = OTPService._get_data(user_id)

        if data.get('verified'):
            raise ValidationError("Kod allaqachon tasdiqlangan")

        attempts = data.get('attempts', 0)

        if attempts >= MAX_ATTEMPTS:
            raise ValidationError("Juda ko'p noto'g'ri urinish! Bloklandingiz.")

        if data['otp'] != _hash_otp(raw_otp):
            data['attempts'] = attempts + 1
            ttl = r.ttl(key)
            if ttl <= 0:
                ttl = OTP_TTL
            r.setex(key, ttl, json.dumps(data))
            raise ValidationError("Kiritilgan tasdiqlash kodi xato!")

        data['verified'] = True
        ttl = r.ttl(key)
        if ttl is None or ttl <= 0:
            ttl = OTP_TTL
        r.setex(key, ttl, json.dumps(data))
        return True

    @staticmethod
    def get_verified(user_id: str):
        data = OTPService._get_data(user_id)
        if not data['verified']:
            raise ValidationError("Kod hali tasdiqlanmagan")
        return data

    @staticmethod
    def delete(user_id: str):
        r.delete(OTPService._key(user_id))


class AccountRecoveryService:
    @staticmethod
    def start(user: User, new_phone, method):
        if method not in ['email', 'telegram_bot']:
            raise ValidationError("Noto'g'ri tiklash usuli tanlandi")
        if user.phone == new_phone:
            raise ValidationError("Yangi telefon raqam eski raqam bilan bir xil bo'lishi mumkin emas")
        if User.objects.filter(phone=new_phone).exists():
            raise ValidationError("Bu yangi telefon raqami allaqachon boshqa akkauntga bog'langan")

        existing = r.get(OTPService._key(str(user.id)))
        if existing:
            raise ValidationError("Tasdiqlash kodi allaqachon yuborilgan. Iltimos, biroz kuting")

        if method == "telegram_bot":
            link_token = f"rec_{uuid.uuid4().hex}"
            recovery_data = {
                'user_id': str(user.id),
                'phone': user.phone,
                'new_phone': new_phone,
            }
            r.setex(f"bot_token:{link_token}", OTP_TTL, json.dumps(recovery_data))
            bot_link = f"https://t.me/{BOT_USERNAME}?start={link_token}"

            logger.info(f"Recovery link generated for user {user.id}")

            return {
                "message": "Iltimos, quyidagi havola orqali botga o'tib Start tugmasini bosing.",
                "bot_link": bot_link,
                "step": "awaiting_bot_start"
            }

        if not user.email:
            raise ValidationError("Akkauntingizga email biriktirilmagan. Bot orqali tiklashdan foydalaning.")

        otp_code = str(random.randint(100000, 999999))
        payload = {
            'otp': _hash_otp(otp_code),
            'new_phone': new_phone,
            'method': method,
            'verified': False,
            'attempts': 0,
        }

        r.setex(OTPService._key(str(user.id)), OTP_TTL, json.dumps(payload))
        logger.info(f"Recovery started via email for user {user.id}")

        try:
            send_mail(
                subject="Akkauntni tiklash tasdiqlash kodi",
                message=f"Sizning parolni tiklash uchun tasdiqlash kodingiz: {otp_code}\nUshbu kod 5 daqiqa davomida faol bo'ladi.",
                from_email=django_settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            r.delete(OTPService._key(str(user.id)))
            logger.error(f"Email yuborishda xatolik yuz berdi: {str(e)}")
            raise ValidationError("Emailga kod yuborishda texnik xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")

        response = {
            "message": "Emailingizga tasdiqlash kodi yuborildi.",
            "step": "awaiting_otp_verify"
        }

        if django_settings.DEBUG:
            response['otp_for_dev'] = otp_code

        return response

    @staticmethod
    def verify(user: User, raw_otp: str):
        OTPService.verify(str(user.id), raw_otp)
        return {"message": "Kod muvaffaqiyatli tasdiqlandi"}

    @staticmethod
    def complete(user: User, new_password: str) -> User:
        data = OTPService.get_verified(str(user.id))

        user.phone = data["new_phone"]
        user.set_password(new_password)
        user.save(update_fields=["phone", "password", "updated_at"])

        OTPService.delete(str(user.id))
        return user