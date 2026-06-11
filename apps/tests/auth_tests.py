from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        phone="+998940000101",
        first_name="Admin",
        last_name="SuperAdmin",
        is_active=True,
        is_superuser=True,
        is_staff=True,
    )
    user.set_password("123m")
    user.save()
    return user


@pytest.mark.django_db
class TestRegister:
    def test_register_start_success(self, api_client):
        url = "/api/v1/auth/register/"

        with patch("apps.service.redis_otp.OTPService.start_registration") as mock_otp:
            mock_otp.return_value = {
                "message": "OTP kod yuborildi",
                "status": "success",
            }

            response = api_client.post(
                url,
                {
                    "phone": "+998902223344",
                    "email": "new@test.com",
                    "method": "telegram_bot",
                    "first_name": "Ali",
                    "last_name": "Valiyev",
                    "password": "NewPassword123!",
                    "confirm_password": "NewPassword123!",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.data["status"] == "success"
            mock_otp.assert_called_once()

    def test_register_different_passwords(self, api_client):
        url = "/api/v1/auth/register/"
        response = api_client.post(
            url,
            {
                "phone": "+998902223344",
                "first_name": "Ali",
                "last_name": "Valiyev",
                "password": "NewPassword123!",
                "confirm_password": "WrongPassword123!",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "confirm_password" in response.data

    def test_register_verify_success(self, api_client):
        url = "/api/v1/auth/register/verify/"

        fake_user = User.objects.create_user(
            phone="+998905556677", password="SomePassword123!"
        )

        with patch(
            "apps.service.redis_otp.OTPService.complete_registration"
        ) as mock_verify:
            mock_verify.return_value = fake_user

            response = api_client.post(url, {"phone": "+998905556677", "otp": "1234"})

            assert response.status_code == status.HTTP_200_OK
            assert "access" in response.data
            assert "refresh" in response.data
            assert response.data["message"] == "Muvaffaqiyatli ro'yxatdan o'tdingiz!"


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, client_user):
        url = "/api/v1/auth/login/"
        response = api_client.post(url, {"phone": "+998940000101", "password": "123m"})
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data
        assert response.data["user"]["phone"] == "+998940000101"

    def test_login_wrong_password(self, api_client, client_user):
        url = "/api/v1/auth/login/"
        response = api_client.post(
            url, {"phone": "+998940000101", "password": "wrong_password_123m"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Telefon raqam yoki parol xato." in str(response.data)
