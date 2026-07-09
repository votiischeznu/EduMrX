from datetime import date, time
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.models import Branch, Course, Group, Payment, Room, Student, Teacher, User
from models import Center


@pytest.fixture
def branch_a(center):
    return Branch.objects.create(
        center=center, name="Chilonzor IT Akademiyasi", address="Chilonzor",
        phone="998901112233", latitude=Decimal("41.0"), longitude=Decimal("69.0"),
    )

@pytest.fixture
def branch_b(center):
    return Branch.objects.create(
        center=center, name="Yunusobod Hub", address="Yunusobod",
        phone="998904445566", latitude=Decimal("41.3"), longitude=Decimal("69.3"),
    )

@pytest.fixture
def other_branch(center):
    other_dir = User.objects.create_user(phone="998905555555", role=User.Role.DIRECTOR)
    other_c = Center.objects.create(name="Begona Markaz", slug="begona", director=other_dir)
    return Branch.objects.create(center=other_c, name="Begona Filial", phone="998909998877")

@pytest.fixture
def group(center):
    course = Course.objects.create(name="Python", duration_months=10, price="2000000", center=center)
    teacher = Teacher.objects.create(user=User.objects.create_user(phone="998902222222", role=User.Role.TEACHER), centers=center)
    room = Room.objects.create(center=center, name="101", capacity=20)
    return Group.objects.create(
        name="Frontend-01", course=course, teacher=teacher, room=room, center=center,
        start_date=date.today(), lesson_days=[0], lesson_start_time=time(9, 0), lesson_end_time=time(10, 0),
    )

def make_student(center, branch=None, phone="998903333333"):
    user = User.objects.create_user(phone=phone, first_name="Ali", last_name="Student", role=User.Role.STUDENT)
    return Student.objects.create(user=user, center=center, branch=branch)

def make_payment(student, group=None, amount="500000"):
    val = Decimal(amount)
    return Payment.objects.create(
        student=student,
        group=group,
        amount=val,
        final_amount=val,
        status=Payment.Status.PAID,
        paid_at=timezone.now(),
        period_month=timezone.now().month,
        period_year=timezone.now().year,
        due_date=date.today(),
        receipt_number=f"REC-{student.id}-{amount}-{timezone.now().timestamp()}",
    )

@pytest.mark.django_db
class TestDirectorAnalyticsSummary:
    def test_summary_response_shape(self, api_client, director_user, center, branch_a, group):
        student = make_student(center, branch=branch_a)
        make_payment(student, group=group)
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-analytics-summary"))
        assert response.status_code == status.HTTP_200_OK

    def test_summary_filtered_by_branch(self, api_client, director_user, center, branch_a, branch_b, group):
        student_a = make_student(center, branch=branch_a, phone="998903333331")
        student_b = make_student(center, branch=branch_b, phone="998903333332")
        make_payment(student_a, group=group, amount="500000")
        make_payment(student_b, group=group, amount="900000")
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-analytics-summary"), {"branch_id": branch_a.id})
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["data"]["month_revenue"]) == 500000.0

@pytest.mark.django_db
class TestDirectorAnalyticsChart:
    def test_chart_response_shape(self, api_client, director_user, center, branch_a, group):
        student = make_student(center, branch=branch_a)
        make_payment(student, group=group)
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-analytics-chart"))
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestDirectorAnalyticsTransactions:
    def test_transactions_response_shape(self, api_client, director_user, center, branch_a, group):
        student = make_student(center, branch=branch_a)
        make_payment(student, group=group)
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-analytics-transactions"))
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestDirectorAnalyticsBranchesList:
    def test_branches_tab_response_shape(self, api_client, director_user, center, branch_a):
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-analytics-branches"))
        assert response.status_code == status.HTTP_200_OK

    def test_centers_response_shape(self, api_client, director_user, center, branch_a, group):
        student = make_student(center, branch=branch_a)
        make_payment(student, group=group)
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("director-analytics-centers"))
        assert response.status_code == status.HTTP_200_OK