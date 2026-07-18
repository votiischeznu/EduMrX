"""
Umumiy (barcha test fayllar uchun) fixture'lar.

Bu fayl `apps/tests/` papkasida joylashgan barcha test modullari uchun
avtomatik ravishda pytest tomonidan yuklanadi (conftest.py bo'lgani uchun
import qilish shart emas).

MUHIM: Agar biror test faylida shu nomdagi fixture boshqacha
ta'rif (masalan qo'shimcha `branch` argumenti) bilan kerak bo'lsa, o'sha
faylning ichida xuddi shu nom bilan fixture yozib qo'yish yetarli --
pytest fixture override mexanizmi tufayli local ta'rif ustunlik qiladi.
"""

from datetime import date, time

import pytest
from rest_framework.test import APIClient

from apps.models import (
    Branch,
    Center,
    Course,
    Group,
    Lesson,
    Room,
    Student,
    Teacher,
    User,
)

# ===========================================================================
# Umumiy: API client
# ===========================================================================


@pytest.fixture
def api_client():
    return APIClient()


# ===========================================================================
# Foydalanuvchilar
# ===========================================================================


@pytest.fixture
def director_user():
    user = User.objects.create_user(
        phone="998901111111",
        first_name="Vali",
        last_name="Valijonov",
        role=User.Role.DIRECTOR,
        is_active=True,
    )
    user.set_password("123m")
    user.save()
    return user


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
    user.role = User.Role.SUPER_ADMIN
    user.save()
    return user


@pytest.fixture
def teacher_user():
    user = User.objects.create_user(
        phone="998902222222",
        first_name="Sherzod",
        last_name="O'qituvchi",
        role=User.Role.TEACHER,
        is_active=True,
    )
    user.set_password("123m")
    user.save()
    return user


# ===========================================================================
# Markaz / Filial / Kurs / O'qituvchi / Xona / Guruh / Dars
# ===========================================================================


@pytest.fixture
def center(director_user):
    return Center.objects.create(
        name="EduMRX Test Markaz",
        slug="edumrx-test-markaz",
        director=director_user,
    )


@pytest.fixture
def branch(center):
    return Branch.objects.create(name="Asosiy filial", center=center, latitude=0.0, longitude=0.0)


@pytest.fixture
def course(center):
    return Course.objects.create(
        name="Python",
        duration_months=10,
        price="2000000",
        status=Course.Status.ACTIVE,
        center=center,
    )


@pytest.fixture
def room(center):
    return Room.objects.create(center=center, name="101", capacity=20)


@pytest.fixture
def teacher(teacher_user, center):
    """ForeignKey bo'lgani uchun to'g'ridan-to'g'ri o'rnatamiz."""
    return Teacher.objects.create(user=teacher_user, centers=center)


@pytest.fixture
def group(center, course, teacher, room):
    return Group.objects.create(
        name="Frontend-01",
        course=course,
        teacher=teacher,
        room=room,
        center=center,
        start_date=date.today(),
        lesson_days=[0],
        lesson_start_time=time(9, 0),
        lesson_end_time=time(10, 0),
    )


@pytest.fixture
def lesson(group):
    return Lesson.objects.create(
        group=group,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(10, 0),
    )


# ===========================================================================
# O'quvchilar
# ===========================================================================


@pytest.fixture
def student_in_center(center):
    user = User.objects.create_user(
        phone="998903333333",
        first_name="Ali",
        last_name="Student",
        role=User.Role.STUDENT,
    )
    return Student.objects.create(user=user, center=center)


@pytest.fixture
def student_in_other_center(other_center):
    user = User.objects.create_user(
        phone="998904444444",
        first_name="Vali",
        last_name="Other",
        role=User.Role.STUDENT,
    )
    return Student.objects.create(user=user, center=other_center)
