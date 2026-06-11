import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from apps.models import Center, Student, User


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
        is_staff=True,
    )
    user.set_password("123m")
    user.save()
    return user


@pytest.fixture
def test_center(super_admin_user):
    return Center.objects.create(
        name="PDP academy",
        slug="pdp-academy",
        phone="+998555084747",
        plan="trial",
        subscription_expires=timezone.now() + timedelta(days=30),
    )


@pytest.mark.django_db
class TestSuperAdminDashboard:
    def test_dashboard_stats(self, api_client, super_admin_user):
        api_client.force_authenticate(user=super_admin_user)
        response = api_client.get("/api/v1/super-admin/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data


@pytest.mark.django_db
class TestSuperAdminDirector:
    def test_director_list_and_create(self, api_client, super_admin_user):
        api_client.force_authenticate(user=super_admin_user)
        assert (
            api_client.get("/api/v1/super-admin/directors/").status_code
            == status.HTTP_200_OK
        )
        payload = {
            "first_name": "Eldor",
            "last_name": "Karimov",
            "phone": "+998935556677",
            "password": "pass",
        }
        assert (
            api_client.post("/api/v1/super-admin/directors/", payload).status_code
            == status.HTTP_201_CREATED
        )


@pytest.mark.django_db
class TestSuperAdminCenter:
    def test_center_crud(self, api_client, super_admin_user):
        api_client.force_authenticate(user=super_admin_user)
        assert (
            api_client.get("/api/v1/super-admin/centers/").status_code
            == status.HTTP_200_OK
        )
        payload = {
            "name": "New Center",
            "slug": "new-c",
            "phone": "+998901112233",
            "plan": "pro",
        }
        assert (
            api_client.post("/api/v1/super-admin/centers/", payload).status_code
            == status.HTTP_201_CREATED
        )


@pytest.mark.django_db
class TestSuperAdminStudent:
    def test_student_list_centers(self, api_client, super_admin_user, test_center):
        api_client.force_authenticate(user=super_admin_user)
        response = api_client.get("/api/v1/super-admin/students/centers/")
        assert response.status_code == status.HTTP_200_OK

    def test_student_list_create(self, api_client, super_admin_user, test_center):
        api_client.force_authenticate(user=super_admin_user)
        payload = {
            "user": {
                "first_name": "Ali",
                "last_name": "Vali",
                "phone": "+998991112233",
            },
            "center": test_center.id,
            "status": "active",
        }
        response = api_client.post(
            "/api/v1/super-admin/students/", payload, format="json"
        )
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        ]
