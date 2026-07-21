import json
from unittest.mock import patch
import pytest
import fakeredis
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from apps.models import User
from apps.service.redis_otp import (
    OTPService,
    AccountRecoveryService,
    _hash_otp,
)

# Use a shared fakeredis instance
shared_redis = fakeredis.FakeRedis(decode_responses=True)

@pytest.fixture(autouse=True)
def mock_redis():
    with patch("apps.service.redis_otp.r", shared_redis):
        shared_redis.flushall()
        yield shared_redis
        shared_redis.flushall()

@pytest.mark.django_db
class TestRedisOTPService:
    def test_init_exception(self):
        with patch("redis.Redis.from_url", side_effect=Exception("Redis error")):
            # Simulate reloading the module to trigger the try-except block
            import importlib
            import apps.service.redis_otp
            importlib.reload(apps.service.redis_otp)
            assert isinstance(apps.service.redis_otp.r, fakeredis.FakeRedis)
            # Restore to fakeredis for other tests
            apps.service.redis_otp.r = fakeredis.FakeRedis(decode_responses=True)

    def test_hash_otp(self):
        assert _hash_otp("1234") == "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"

    def test_start_registration_telegram_bot(self):
        registration_data = {
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "SecurePassword123",
        }
        res = OTPService.start_registration(
            phone="+998901112233",
            email="ali@test.com",
            method="telegram_bot",
            registration_data=registration_data,
        )

        assert "bot_link" in res
        assert "awaiting_bot_start" in res["step"]

        # Verify redis keys
        key = OTPService._key("+998901112233")
        stored = json.loads(shared_redis.get(key))
        assert stored["phone"] == "+998901112233"
        assert stored["email"] == "ali@test.com"
        assert stored["first_name"] == "Ali"
        assert stored["last_name"] == "Valiyev"

    @patch("apps.service.redis_otp.send_mail")
    def test_start_registration_email_success(self, mock_send_mail):
        registration_data = {
            "first_name": "Vali",
            "password": "Password123",
        }
        res = OTPService.start_registration(
            phone="+998901112244",
            email="vali@test.com",
            method="email",
            registration_data=registration_data,
        )

        assert "Emailingizga tasdiqlash kodi" in res["message"]
        assert res["step"] == "awaiting_otp_verify"
        mock_send_mail.assert_called_once()

    @patch("apps.service.redis_otp.send_mail")
    def test_start_registration_email_failure(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP error")
        registration_data = {
            "first_name": "ErrorCase",
            "password": "Password123",
        }
        with pytest.raises(ValidationError) as excinfo:
            OTPService.start_registration(
                phone="+998901112255",
                email="error@test.com",
                method="email",
                registration_data=registration_data,
            )
        assert "Emailga kod yuborishda xatolik" in str(excinfo.value)
        # Verify redis key deleted on failure
        key = OTPService._key("+998901112255")
        assert shared_redis.get(key) is None

    def test_complete_registration_expired_session(self):
        with pytest.raises(ValidationError) as excinfo:
            OTPService.complete_registration("+998901112266", "1234")
        assert "Tasdiqlash muddati tugagan" in str(excinfo.value)

    def test_complete_registration_max_attempts(self):
        key = OTPService._key("+998901112266")
        payload = {
            "otp": _hash_otp("1234"),
            "phone": "+998901112266",
            "email": "test@test.com",
            "password": "Pass",
            "attempts": 5,
        }
        shared_redis.set(key, json.dumps(payload))

        with pytest.raises(ValidationError) as excinfo:
            OTPService.complete_registration("+998901112266", "1234")
        assert "Urinishlar soni tugadi" in str(excinfo.value)
        assert shared_redis.get(key) is None

    def test_complete_registration_wrong_otp(self):
        key = OTPService._key("+998901112266")
        payload = {
            "otp": _hash_otp("1234"),
            "phone": "+998901112266",
            "email": "test@test.com",
            "password": "Pass",
            "attempts": 1,
        }
        shared_redis.set(key, json.dumps(payload))

        with pytest.raises(ValidationError) as excinfo:
            OTPService.complete_registration("+998901112266", "9999")
        assert "Tasdiqlash kodi noto'g'ri" in str(excinfo.value)

        # Verify attempts incremented
        stored = json.loads(shared_redis.get(key))
        assert stored["attempts"] == 2

    def test_complete_registration_success_no_telegram(self):
        key = OTPService._key("+998901112277")
        payload = {
            "otp": _hash_otp("1234"),
            "phone": "+998901112277",
            "email": "success@test.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePassword123",
            "attempts": 0,
        }
        shared_redis.set(key, json.dumps(payload))

        user = OTPService.complete_registration("+998901112277", "1234")
        assert user.phone == "+998901112277"
        assert user.email == "success@test.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_active is True
        assert shared_redis.get(key) is None

    def test_complete_registration_success_with_telegram_not_taken(self):
        key = OTPService._key("+998901112288")
        payload = {
            "otp": _hash_otp("1234"),
            "phone": "+998901112288",
            "email": "tg@test.com",
            "password": "SecurePassword123",
            "attempts": 0,
            "telegram_chat_id": 123456789,
            "telegram_username": "tg_user",
        }
        shared_redis.set(key, json.dumps(payload))

        user = OTPService.complete_registration("+998901112288", "1234")
        assert user.telegram_id == 123456789
        assert user.telegram_username == "tg_user"
        assert user.telegram_linked_at is not None

    def test_complete_registration_success_with_telegram_already_taken(self):
        # Create an existing user with the same telegram_id
        User.objects.create_user(phone="+998901110000", password="SomePassword", telegram_id=987654321)

        key = OTPService._key("+998901112299")
        payload = {
            "otp": _hash_otp("1234"),
            "phone": "+998901112299",
            "email": "tg2@test.com",
            "password": "SecurePassword123",
            "attempts": 0,
            "telegram_chat_id": 987654321,
            "telegram_username": "tg_user2",
        }
        shared_redis.set(key, json.dumps(payload))

        user = OTPService.complete_registration("+998901112299", "1234")
        # Should not link because already taken
        assert user.telegram_id is None

    def test_complete_registration_success_with_telegram_integrity_error(self):
        key = OTPService._key("+998901112200")
        payload = {
            "otp": _hash_otp("1234"),
            "phone": "+998901112200",
            "email": "tg_ie@test.com",
            "password": "SecurePassword123",
            "attempts": 0,
            "telegram_chat_id": 111222333,
            "telegram_username": "tg_user_ie",
        }
        shared_redis.set(key, json.dumps(payload))

        # We want user.save() to raise IntegrityError the first time to simulate a race condition,
        # but succeed the second time (when telegram fields are cleared).
        original_create_user = User.objects.create_user

        def mock_create_user(*args, **kwargs):
            user_obj = original_create_user(*args, **kwargs)
            original_save = user_obj.save

            def mock_save(*s_args, **s_kwargs):
                if not hasattr(mock_save, "called"):
                    mock_save.called = True
                    raise IntegrityError("mock integrity error")
                return original_save(*s_args, **s_kwargs)

            user_obj.save = mock_save
            return user_obj

        with patch("apps.models.User.objects.create_user", side_effect=mock_create_user):
            user = OTPService.complete_registration("+998901112200", "1234")
            assert user.telegram_id is None
            assert user.telegram_username == ""
            assert user.telegram_linked_at is None


@pytest.mark.django_db
class TestAccountRecoveryService:
    def test_start_recovery_telegram_bot(self):
        user = User.objects.create_user(phone="+998903334455", password="Password123")
        res = AccountRecoveryService.start(user, "+998903334466", "telegram_bot")

        assert "bot_link" in res
        assert "awaiting_bot_start" in res["step"]

        key = OTPService._key(str(user.id))
        stored = json.loads(shared_redis.get(key))
        assert stored["new_phone"] == "+998903334466"
        assert stored["purpose"] == "recovery"

    @patch("apps.service.redis_otp.send_mail")
    def test_start_recovery_email_success(self, mock_send_mail):
        user = User.objects.create_user(phone="+998903334477", email="recovery@test.com", password="Password123")
        res = AccountRecoveryService.start(user, "+998903334488", "email")

        assert "Emailingizga tasdiqlash kodi" in res["message"]
        assert res["step"] == "awaiting_otp_verify"
        mock_send_mail.assert_called_once()

    def test_start_recovery_email_no_email(self):
        user = User.objects.create_user(phone="+998903334499", password="Password123")  # no email
        with pytest.raises(ValidationError) as excinfo:
            AccountRecoveryService.start(user, "+998903334400", "email")
        assert "email bog'lanmagan" in str(excinfo.value)

    @patch("apps.service.redis_otp.send_mail")
    def test_start_recovery_email_failure(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP down")
        user = User.objects.create_user(phone="+998903334411", email="fail@test.com", password="Password123")
        with pytest.raises(ValidationError) as excinfo:
            AccountRecoveryService.start(user, "+998903334422", "email")
        assert "Emailga kod yuborishda xatolik" in str(excinfo.value)
        assert shared_redis.get(OTPService._key(str(user.id))) is None

    def test_verify_recovery_expired_session(self):
        user = User.objects.create_user(phone="+998903334433", password="Password123")
        with pytest.raises(ValidationError) as excinfo:
            AccountRecoveryService.verify(user, "123456")
        assert "Muddati tugagan seans" in str(excinfo.value)

    def test_verify_recovery_max_attempts(self):
        user = User.objects.create_user(phone="+998903334444", password="Password123")
        key = OTPService._key(str(user.id))
        payload = {
            "otp": _hash_otp("123456"),
            "new_phone": "+998903334445",
            "attempts": 5,
        }
        shared_redis.set(key, json.dumps(payload))

        with pytest.raises(ValidationError) as excinfo:
            AccountRecoveryService.verify(user, "123456")
        assert "Urinishlar soni tugadi" in str(excinfo.value)
        assert shared_redis.get(key) is None

    def test_verify_recovery_wrong_otp(self):
        user = User.objects.create_user(phone="+998903334455", password="Password123")
        key = OTPService._key(str(user.id))
        payload = {
            "otp": _hash_otp("123456"),
            "new_phone": "+998903334456",
            "attempts": 1,
        }
        shared_redis.set(key, json.dumps(payload))

        with pytest.raises(ValidationError) as excinfo:
            AccountRecoveryService.verify(user, "999999")
        assert "Kod noto'g'ri" in str(excinfo.value)

        stored = json.loads(shared_redis.get(key))
        assert stored["attempts"] == 2

    def test_verify_recovery_success(self):
        user = User.objects.create_user(phone="+998903334466", password="Password123")
        key = OTPService._key(str(user.id))
        payload = {
            "otp": _hash_otp("123456"),
            "new_phone": "+998903334467",
            "attempts": 0,
            "verified": False,
        }
        shared_redis.set(key, json.dumps(payload))

        res = AccountRecoveryService.verify(user, "123456")
        assert "muvaffaqiyatli tasdiqlandi" in res["message"]

        stored = json.loads(shared_redis.get(key))
        assert stored["verified"] is True

    def test_complete_recovery_no_session(self):
        user = User.objects.create_user(phone="+998903334477", password="Password123")
        with pytest.raises(ValidationError) as excinfo:
            AccountRecoveryService.complete(user, "NewPass123!")
        assert "Tiklash seansi topilmadi" in str(excinfo.value)

    def test_complete_recovery_not_verified(self):
        user = User.objects.create_user(phone="+998903334488", password="Password123")
        key = OTPService._key(str(user.id))
        payload = {
            "otp": _hash_otp("123456"),
            "new_phone": "+998903334489",
            "verified": False,
        }
        shared_redis.set(key, json.dumps(payload))

        with pytest.raises(ValidationError) as excinfo:
            AccountRecoveryService.complete(user, "NewPass123!")
        assert "Kod hali tasdiqlanmagan" in str(excinfo.value)

    def test_complete_recovery_success(self):
        user = User.objects.create_user(phone="+998903334499", password="Password123")
        key = OTPService._key(str(user.id))
        payload = {
            "otp": _hash_otp("123456"),
            "new_phone": "+998903334400",
            "verified": True,
        }
        shared_redis.set(key, json.dumps(payload))

        updated_user = AccountRecoveryService.complete(user, "NewPass1234!")
        assert updated_user.phone == "+998903334400"
        assert updated_user.check_password("NewPass1234!") is True
        assert shared_redis.get(key) is None