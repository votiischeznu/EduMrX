"""
Director Student va Teacher endpointlari uchun testlar.

Ishga tushirish:
    pytest apps/tests/test_director_student_teacher.py -v
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.models import Center, Student, Teacher, User


@pytest.fixture
def other_director():
    """Boshqa direktyor — ruxsatsiz amallar testlari uchun."""
    user = User.objects.create_user(
        phone="998905555555",
        first_name="Boshqa",
        last_name="Direktor",
        role=User.Role.DIRECTOR,
        is_active=True,
    )
    user.set_password("123m")
    user.save()
    return user


@pytest.fixture
def other_center(other_director):
    """Bu fayl uchun mahalliy: boshqa direktorga tegishli markaz.
    conftest.py dagi `student_in_other_center` fixture'i aynan shu
    `other_center` ga bog'lanadi (pytest fixture override mexanizmi)."""
    return Center.objects.create(
        name="Boshqa Markaz",
        slug="boshqa-markaz",
        director=other_director,
    )


# ===========================================================================
# Teacher testlari
# ===========================================================================


@pytest.mark.django_db
class TestDirectorTeacherList:
    def test_list_own_teachers(self, api_client, director_user, teacher):
        """Director faqat o'z markazidagi o'qituvchilarni ko'radi."""
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-teachers-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [t["id"] for t in response.data["results"]]
        assert str(teacher.id) in ids

    def test_other_center_teacher_not_visible(self, api_client, director_user, other_center):
        """Boshqa markazdagi o'qituvchi ro'yxatda ko'rinmasligi kerak."""
        other_user = User.objects.create_user(phone="998906666666", role=User.Role.TEACHER)
        other_teacher = Teacher.objects.create(user=other_user)
        other_teacher.centers = other_center
        other_teacher.save()

        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-teachers-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [t["id"] for t in response.data["results"]]
        assert str(other_teacher.id) not in ids

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse("director-teachers-list-create"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDirectorTeacherCreate:
    def test_create_teacher_success(self, api_client, director_user, center):
        """To'liq ma'lumot bilan teacher yaratish muvaffaqiyatli bo'lishi kerak."""
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": "998901234567",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "securepassword",
            "center": str(center.id),
            "salary": "1000000.00",
            "experience": 3,
            "specialization": "Backend",
        }
        response = api_client.post(reverse("director-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Teacher.objects.filter(user__first_name="Ali").exists()
        teacher = Teacher.objects.get(user__first_name="Ali")
        # Avval qiymat mavjudligini tekshiring
        assert teacher.centers is not None, "Teacher center maydoni None bo'lib qoldi!"
        assert teacher.centers.id == center.id

    def test_create_teacher_without_password_fails(self, api_client, director_user, center):
        """password majburiy field — bo'lmasa 400 qaytishi kerak."""
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": "998901234568",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "center": str(center.id),
        }
        response = api_client.post(reverse("director-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_create_teacher_invalid_salary_fails(self, api_client, director_user, center):
        """max_digits=12 chegarasidan oshsa 400 qaytishi kerak."""
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": "998901234569",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "password",
            "center": str(center.id),
            "salary": "9999999999999999",
        }
        response = api_client.post(reverse("director-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "salary" in response.data

    def test_create_teacher_duplicate_phone_fails(self, api_client, director_user, center, teacher):
        """Mavjud telefon bilan teacher yaratish 400 qaytishi kerak."""
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": teacher.user.phone,  # allaqachon mavjud
            "first_name": "Yangi",
            "last_name": "Teacher",
            "password": "password",
            "center": str(center.id),
        }
        response = api_client.post(reverse("director-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data

    def test_create_teacher_other_center_forbidden(self, api_client, director_user, other_center):
        """Boshqa direktorning markaziga teacher yaratish 403 qaytishi kerak."""
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": "998907777777",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "password",
            "center": str(other_center.id),
        }
        response = api_client.post(reverse("director-teachers-list-create"), payload, format="json")
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ]


@pytest.mark.django_db
class TestDirectorTeacherDetail:
    def test_retrieve_teacher(self, api_client, director_user, teacher):
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-teachers-detail", kwargs={"pk": teacher.id}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(teacher.id)

    def test_retrieve_other_center_teacher_returns_404(self, api_client, director_user, other_center):
        other_user = User.objects.create_user(phone="998908888888", role=User.Role.TEACHER)
        other_teacher = Teacher.objects.create(user=other_user)
        other_teacher.centers = other_center
        other_teacher.save()

        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-teachers-detail", kwargs={"pk": other_teacher.id}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_teacher_first_name(self, api_client, director_user, teacher):
        api_client.force_authenticate(user=director_user)
        payload = {"first_name": "Yangilangan"}
        response = api_client.patch(
            reverse("director-teachers-detail", kwargs={"pk": teacher.id}), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        teacher.user.refresh_from_db()
        assert teacher.user.first_name == "Yangilangan"

    def test_update_teacher_specialization(self, api_client, director_user, teacher):
        api_client.force_authenticate(user=director_user)
        payload = {"specialization": "Frontend"}
        response = api_client.patch(
            reverse("director-teachers-detail", kwargs={"pk": teacher.id}), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        teacher.refresh_from_db()
        assert teacher.specialization == "Frontend"

    def test_soft_delete_teacher(self, api_client, director_user, teacher):
        api_client.force_authenticate(user=director_user)
        response = api_client.delete(reverse("director-teachers-detail", kwargs={"pk": teacher.id}))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        teacher.user.refresh_from_db()
        assert teacher.user.is_deleted is True
        assert teacher.user.is_active is False

    def test_deleted_teacher_not_in_list(self, api_client, director_user, teacher):
        """Soft-delete qilingan teacher ro'yxatda ko'rinmasligi kerak."""
        teacher.user.is_deleted = True
        teacher.user.is_active = False
        teacher.user.save()

        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-teachers-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [t["id"] for t in response.data["results"]]
        assert str(teacher.id) not in ids


# ===========================================================================
# Student testlari
# ===========================================================================


@pytest.mark.django_db
class TestDirectorStudentList:
    def test_list_own_students(self, api_client, director_user, student_in_center):
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-students-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [s["id"] for s in response.data["results"]]
        assert str(student_in_center.id) in ids

    def test_other_center_student_not_visible(self, api_client, director_user, student_in_other_center):
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-students-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [s["id"] for s in response.data["results"]]
        assert str(student_in_other_center.id) not in ids

    def test_search_by_first_name(self, api_client, director_user, student_in_center):
        api_client.force_authenticate(user=director_user)
        response = api_client.get(
            reverse("director-students-list-create"), {"search": student_in_center.user.first_name}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse("director-students-list-create"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDirectorStudentCreate:
    def test_create_student_success(self, api_client, director_user, center):
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": "998909998877",
            "first_name": "Yangi",
            "last_name": "Student",
            "center": str(center.id),
            "status": "active",
        }
        response = api_client.post(reverse("director-students-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Student.objects.filter(user__phone="998909998877").exists()

    def test_create_student_with_all_fields(self, api_client, director_user, center, branch):
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": "998909998866",
            "first_name": "To'liq",
            "last_name": "Ma'lumot",
            "password": "password123",
            "center": str(center.id),
            "branch": str(branch.id),
            "date_of_birth": "2005-03-15",
            "notes": "Test eslatma",
            "status": "active",
        }
        response = api_client.post(reverse("director-students-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        student = Student.objects.get(user__phone="998909998866")
        assert student.branch_id == branch.id
        assert str(student.date_of_birth) == "2005-03-15"

    def test_create_student_duplicate_phone_fails(self, api_client, director_user, center, student_in_center):
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": student_in_center.user.phone,  # allaqachon mavjud
            "first_name": "Test",
            "last_name": "Test",
            "center": str(center.id),
        }
        response = api_client.post(reverse("director-students-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data

    def test_create_student_other_center_forbidden(self, api_client, director_user, other_center):
        api_client.force_authenticate(user=director_user)
        payload = {
            "phone": "998909998855",
            "first_name": "Test",
            "last_name": "Test",
            "center": str(other_center.id),
        }
        response = api_client.post(reverse("director-students-list-create"), payload, format="json")
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_create_student_missing_phone_fails(self, api_client, director_user, center):
        api_client.force_authenticate(user=director_user)
        payload = {
            "first_name": "Test",
            "last_name": "Test",
            "center": str(center.id),
        }
        response = api_client.post(reverse("director-students-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data


@pytest.mark.django_db
class TestDirectorStudentDetail:
    def test_retrieve_student(self, api_client, director_user, student_in_center):
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-students-detail", kwargs={"pk": student_in_center.id}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(student_in_center.id)

    def test_retrieve_other_center_student_returns_404(self, api_client, director_user, student_in_other_center):
        api_client.force_authenticate(user=director_user)
        response = api_client.get(
            reverse("director-students-detail", kwargs={"pk": student_in_other_center.id})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_student_first_name(self, api_client, director_user, student_in_center):
        api_client.force_authenticate(user=director_user)
        payload = {"first_name": "Yangi Ism"}
        response = api_client.patch(
            reverse("director-students-detail", kwargs={"pk": student_in_center.id}), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        student_in_center.user.refresh_from_db()
        assert student_in_center.user.first_name == "Yangi Ism"

    def test_update_student_status(self, api_client, director_user, student_in_center):
        api_client.force_authenticate(user=director_user)
        payload = {"status": "inactive"}
        response = api_client.patch(
            reverse("director-students-detail", kwargs={"pk": student_in_center.id}), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        student_in_center.refresh_from_db()
        assert student_in_center.status == "inactive"

    def test_update_student_response_has_detail_fields(self, api_client, director_user, student_in_center):
        """
        PATCH response'da DetailSerializer fieldlari bo'lishi kerak
        (notes, date_of_birth va boshqalar).
        """
        api_client.force_authenticate(user=director_user)
        payload = {"notes": "Yangi eslatma"}
        response = api_client.patch(
            reverse("director-students-detail", kwargs={"pk": student_in_center.id}), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        # DetailSerializer fieldlari borligini tekshiramiz
        assert "notes" in response.data
        assert "date_of_birth" in response.data

    def test_soft_delete_student(self, api_client, director_user, student_in_center):
        api_client.force_authenticate(user=director_user)
        response = api_client.delete(reverse("director-students-detail", kwargs={"pk": student_in_center.id}))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        student_in_center.user.refresh_from_db()
        assert student_in_center.user.is_deleted is True
        assert student_in_center.user.is_active is False

    def test_deleted_student_not_in_list(self, api_client, director_user, student_in_center):
        """Soft-delete qilingan student ro'yxatda ko'rinmasligi kerak."""
        student_in_center.user.is_deleted = True
        student_in_center.user.is_active = False
        student_in_center.user.save()

        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-students-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [s["id"] for s in response.data["results"]]
        assert str(student_in_center.id) not in ids

    def test_put_method_not_allowed(self, api_client, director_user, student_in_center):
        """PUT metodi ruxsat etilmasligi kerak."""
        api_client.force_authenticate(user=director_user)
        response = api_client.put(
            reverse("director-students-detail", kwargs={"pk": student_in_center.id}), {}, format="json"
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED