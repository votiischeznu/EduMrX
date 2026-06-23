import pytest
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.models import ContactMessage


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superadmin_user():
    return baker.make("apps.User", role="superadmin")


@pytest.fixture
def regular_user():
    return baker.make("apps.User", role="teacher")


# ──────────────────────────────────────────────
# CREATE
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestContactMessageCreateView:
    URL = "contact-create"

    def test_create_success(self, api_client, mocker):
        mock_send = mocker.patch("apps.views.contact.send_contact_message_to_telegram")
        payload = {
            "full_name": "Aliyev Vali",
            "phone": "+998901234567",
            "center_name": "EduMrX Test Center",
            "message": "Salom, narxlar haqida ma'lumot bera olasizmi?",
        }

        response = api_client.post(reverse(self.URL), payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert ContactMessage.objects.count() == 1
        assert ContactMessage.objects.first().phone == "998901234567"
        mock_send.assert_called_once()

    def test_phone_normalized_without_country_code(self, api_client, mocker):
        mocker.patch("apps.views.contact.send_contact_message_to_telegram")
        payload = {
            "full_name": "Aliyev Vali",
            "phone": "901234567",
            "message": "Test xabar",
        }

        response = api_client.post(reverse(self.URL), payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert ContactMessage.objects.first().phone == "998901234567"

    def test_invalid_phone_returns_400(self, api_client, mocker):
        mocker.patch("apps.views.contact.send_contact_message_to_telegram")
        payload = {
            "full_name": "Aliyev Vali",
            "phone": "12345",
            "message": "Test xabar",
        }

        response = api_client.post(reverse(self.URL), payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data

    def test_missing_full_name_returns_400(self, api_client, mocker):
        mocker.patch("apps.views.contact.send_contact_message_to_telegram")
        payload = {"phone": "+998901234567", "message": "Test"}

        response = api_client.post(reverse(self.URL), payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "full_name" in response.data

    def test_anonymous_user_can_create(self, api_client, mocker):
        mocker.patch("apps.views.contact.send_contact_message_to_telegram")
        payload = {
            "full_name": "Anonim Foydalanuvchi",
            "phone": "+998901234567",
            "message": "Login qilmasdan yuborilgan xabar",
        }

        response = api_client.post(reverse(self.URL), payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_center_name_is_optional(self, api_client, mocker):
        mocker.patch("apps.views.contact.send_contact_message_to_telegram")
        payload = {
            "full_name": "Test User",
            "phone": "+998901234567",
            "message": "Markaz nomi yo'q",
        }

        response = api_client.post(reverse(self.URL), payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert ContactMessage.objects.first().center_name is None


# ──────────────────────────────────────────────
# LIST
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestSuperAdminContactMessageListView:
    URL = "superadmin-contact-list"

    def test_superadmin_can_list(self, api_client, superadmin_user):
        baker.make(ContactMessage, _quantity=3)
        api_client.force_authenticate(user=superadmin_user)

        response = api_client.get(reverse(self.URL))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_non_superadmin_gets_403(self, api_client, regular_user):
        api_client.force_authenticate(user=regular_user)

        response = api_client.get(reverse(self.URL))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_gets_401_or_403(self, api_client):
        response = api_client.get(reverse(self.URL))

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_ordered_by_newest_first(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)
        older = baker.make(ContactMessage, full_name="Birinchi")
        newer = baker.make(ContactMessage, full_name="Ikkinchi")

        response = api_client.get(reverse(self.URL))

        results = response.data["results"]
        assert results[0]["id"] == newer.id
        assert results[1]["id"] == older.id


# ──────────────────────────────────────────────
# MARK READ
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestSuperAdminContactMessageMarkReadView:
    URL = "superadmin-contact-mark-read"

    def test_superadmin_can_mark_as_read(self, api_client, superadmin_user):
        contact_message = baker.make(ContactMessage, is_read=False)
        api_client.force_authenticate(user=superadmin_user)

        response = api_client.patch(reverse(self.URL, kwargs={"pk": contact_message.id}))

        assert response.status_code == status.HTTP_200_OK
        contact_message.refresh_from_db()
        assert contact_message.is_read is True

    def test_non_superadmin_cannot_mark_read(self, api_client, regular_user):
        contact_message = baker.make(ContactMessage, is_read=False)
        api_client.force_authenticate(user=regular_user)

        response = api_client.patch(reverse(self.URL, kwargs={"pk": contact_message.id}))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        contact_message.refresh_from_db()
        assert contact_message.is_read is False

    def test_mark_nonexistent_message_returns_404(self, api_client, superadmin_user):
        api_client.force_authenticate(user=superadmin_user)

        response = api_client.patch(reverse(self.URL, kwargs={"pk": 99999}))

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ──────────────────────────────────────────────
# CELERY TASK
# ──────────────────────────────────────────────


@pytest.mark.django_db
class TestDeleteOldContactMessagesTask:
    def test_deletes_messages_older_than_30_days(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.tasks.contact import delete_old_contact_messages

        old_message = baker.make(ContactMessage)
        ContactMessage.objects.filter(id=old_message.id).update(created_at=timezone.now() - timedelta(days=31))

        recent_message = baker.make(ContactMessage)

        result = delete_old_contact_messages()

        assert not ContactMessage.objects.filter(id=old_message.id).exists()
        assert ContactMessage.objects.filter(id=recent_message.id).exists()
        assert "Deleted 1" in result

    def test_does_not_delete_recent_messages(self):
        from apps.tasks.contact import delete_old_contact_messages

        baker.make(ContactMessage, _quantity=5)

        result = delete_old_contact_messages()

        assert ContactMessage.objects.count() == 5
        assert "Deleted 0" in result
