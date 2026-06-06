from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.models import Center, Student, User, Payment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def super_admin_user():
    user = User.objects.create_user(
        phone="+998940000101",
        first_name="Admin",
        last_name="SuperAdmin",
        is_active=True,
        is_superuser=True,
        is_staff=True
    )
    user.set_password("123m")
    user.save()
    return user


@pytest.fixture
def director_user():
    user = User.objects.create_user(
        phone="+998940656001",
        first_name="Ali",
        last_name="Valiyev",
        role=User.Role.DIRECTOR,
        is_active=True
    )
    user.set_password("director123")
    user.save()
    return user


@pytest.fixture
def test_center(director_user):
    return Center.objects.create(
        name="PDP",
        slug="pdp",
        phone="+998213121321",
        director=director_user,
        subscription_expires=timezone.now() + timedelta(days=30)
    )



@pytest.mark.django_db
class TestSuperAdminDirector:
    list_url = '/api/v1/super-admin/directors/'

    # Bu qismlar allaqachon muvaffaqiyatli ishlamoqda
    def test_director_list_success(self, api_client, super_admin_user, director_user):
        api_client.force_authenticate(user=super_admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK

    def test_director_create_success(self, api_client, super_admin_user):
        api_client.force_authenticate(user=super_admin_user)
        payload = {
            "first_name": "Eldor", "last_name": "Karimov",
            "phone": "+998935556677", "password": "securepassword123"
        }
        response = api_client.post(self.list_url, payload)
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestSuperAdminCenter:
    list_url = '/api/v1/super-admin/centers/'

    def test_center_list_success(self, api_client, super_admin_user, test_center):
        api_client.force_authenticate(user=super_admin_user)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK



@pytest.mark.django_db
class TestSuperAdminStudentCenterList:
    url = '/api/v1/super-admin/students/centers/'
    def test_student_center_list_counts(self, api_client, super_admin_user, test_center):
        api_client.force_authenticate(user=super_admin_user)
        u1 = User.objects.create(first_name="Xusan", last_name="Yarashov", phone="+998991112233")
        Student.objects.create(user=u1, center=test_center, status="active")
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
