import json
import random

import redis
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.exceptions import ValidationError

from apps.models import User
from root.settings import REDIS_URL

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
OTP_TTL = 60 * 2


class OTPService:

    @staticmethod
    def _key(user_id: str):
        return f"account_recovery:{user_id}"

    @staticmethod
    def _get_data(user_id: str):
        raw = r.get(OTPService._key(user_id))
        if not raw:
            raise ValidationError("Kod muddati utgan yoki mavjud emas")
        return json.loads(raw)

    @staticmethod
    def create(user_id: str, new_phone: str, method: str):
        otp = str(random.randint(100000, 999999))
        data = {
            'otp': make_password(otp),
            'new_phone': new_phone,
            'method': method,
            'verified': False,
        }
        r.setex(OTPService._key(user_id), OTP_TTL, json.dumps(data))
        print("\n" + "=" * 40 + f"\nHaqiqiy OTP kod: {otp}\n" + "=" * 40 + "\n")
        return otp

    @staticmethod
    def verify(user_id: str, raw_otp: str):
        key = OTPService._key(user_id)
        data = OTPService._get_data(user_id)
        if data.get('verified'):
            raise ValidationError("Kod allaqachon tasdiqlangan")
        if not check_password(raw_otp, data['otp']):
            raise ValidationError("Kod xato")
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
    def start(user: User, new_phone: str, method: str):
        if method not in ['email', 'backup_phone']:
            raise ValidationError("Noto'g'ri tiklash usuli")
        if user.phone == new_phone:
            raise ValidationError("Yangi telefon raqam eski raqam bilan bir xil")
        if User.objects.filter(phone=new_phone).exists():
            raise ValidationError("Bu telefon raqam allaqachon mavjud")
        if method == "email" and not user.email:
            raise ValidationError("Email manzilingiz mavjud emas")
        if method == "backup_phone" and not user.backup_phone:
            raise ValidationError("Zahira telefon raqamingiz mavjud emas")

        otp = OTPService.create(str(user.id), new_phone, method)

        if method == "email":
            AccountRecoveryService._send_email(user.email, otp)
        else:
            AccountRecoveryService._send_sms(user.backup_phone, otp)

        return {"message": "Kod muvaffaqiyatli yuborildi"}

    @staticmethod
    def verify(user: User, raw_otp: str):
        OTPService.verify(str(user.id), raw_otp)
        return {"message": "Kod tasdiqlandi"}

    @staticmethod
    def complete(user: User, new_password: str) -> User:
        data = OTPService.get_verified(str(user.id))
        user.phone = data["new_phone"]
        user.set_password(new_password)
        user.save(update_fields=["phone", "password", "updated_at"])
        OTPService.delete(str(user.id))
        return user


    @staticmethod
    def _send_sms(phone: str, otp: str):
        pass

    @staticmethod
    def _send_email(email: str, otp: str):
        pass
