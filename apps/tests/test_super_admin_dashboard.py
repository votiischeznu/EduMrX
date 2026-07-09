from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.models import Center


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
        response = api_client.get(reverse("super-admin-dashboard"))
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data


@pytest.mark.django_db
class TestSuperAdminDirector:
    def test_director_list_and_create(self, api_client, super_admin_user):
        api_client.force_authenticate(user=super_admin_user)
        assert (
            api_client.get(reverse("super-admin-directors-list-create")).status_code
            == status.HTTP_200_OK
        )
        payload = {
            "first_name": "Eldor",
            "last_name": "Karimov",
            "phone": "+998935556677",
            "password": "pass",
        }
        assert (
            api_client.post(reverse("super-admin-directors-list-create"), payload).status_code
            == status.HTTP_201_CREATED
        )


@pytest.mark.django_db
class TestSuperAdminCenter:
    def test_center_crud(self, api_client, super_admin_user):
        api_client.force_authenticate(user=super_admin_user)
        assert (
            api_client.get(reverse("super-admin-centers-list-create")).status_code
            == status.HTTP_200_OK
        )
        payload = {
            "name": "New Center",
            "slug": "new-c",
            "phone": "+998901112233",
            "plan": "pro",
        }
        assert (
            api_client.post(reverse("super-admin-centers-list-create"), payload).status_code
            == status.HTTP_201_CREATED
        )