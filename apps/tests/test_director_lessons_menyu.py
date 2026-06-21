from datetime import date, time, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.models import Center, Course, Group, Room, Teacher, User, Lesson, Student, Attendance


@pytest.fixture
def api_client():
    return APIClient()


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
def center(director_user):
    return Center.objects.create(
        name="EduMRX Test Markaz",
        slug="edumrx-test-markaz",
        director=director_user,
    )


@pytest.fixture
def other_center():
    return Center.objects.create(
        name="Boshqa Markaz",
        slug="boshqa-markaz",
    )


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
def room(center):
    return Room.objects.create(center=center, name="101", capacity=20)


@pytest.fixture
def lesson(group):
    return Lesson.objects.create(group=group, date=date.today(), start_time=time(9, 0), end_time=time(10, 0))


@pytest.fixture
def student_in_center(center):
    user = User.objects.create_user(phone="998903333333", first_name="Ali", last_name="Student", role=User.Role.STUDENT)
    return Student.objects.create(user=user, center=center)


@pytest.fixture
def student_in_other_center(other_center):
    user = User.objects.create_user(phone="998904444444", first_name="Vali", last_name="Other", role=User.Role.STUDENT)
    return Student.objects.create(user=user, center=other_center)


@pytest.fixture
def teacher(teacher_user, center):
    return Teacher.objects.create(user=teacher_user, centers=center)


@pytest.mark.django_db
class TestDirectorCourseView:
    def test_no_center_returns_404_on_create(self, api_client, director_user):
        api_client.force_authenticate(user=director_user)
        payload = {
            "name": "Python",
            "duration_months": 10,
            "price": "2000000",
            "status": "active",
        }
        response = api_client.post("/api/v1/director/courses/", payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_course(self, api_client, director_user, center):
        api_client.force_authenticate(user=director_user)
        payload = {
            "name": "Python",
            "duration_months": 10,
            "price": "2000000",
            "status": "active",
        }
        response = api_client.post("/api/v1/director/courses/", payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert Course.objects.filter(name="Python", center=center).exists()

    def test_list_only_shows_own_center_courses(self, api_client, director_user, center, other_center):
        Course.objects.create(name="Mine", duration_months=1, price="100", center=center)
        Course.objects.create(name="Not Mine", duration_months=1, price="100", center=other_center)

        api_client.force_authenticate(user=director_user)
        response = api_client.get("/api/v1/director/courses/")

        assert response.status_code == status.HTTP_200_OK
        names = [c["name"] for c in response.data.get("results", response.data)]
        assert "Mine" in names
        assert "Not Mine" not in names


@pytest.mark.django_db
class TestDirectorGroupView:
    def test_create_group_attaches_center(self, api_client, director_user, center, course, teacher, room):
        api_client.force_authenticate(user=director_user)
        payload = {
            "name": "Frontend-01",
            "course": str(course.id),
            "teacher": str(teacher.id),
            "room": str(room.id),
            "status": "active",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=180)).isoformat(),
            "lesson_days": [0, 2, 4],
            "lesson_start_time": time(9, 0).isoformat(),
            "lesson_end_time": time(11, 0).isoformat(),
        }
        response = api_client.post("/api/v1/director/groups/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        group = Group.objects.get(name="Frontend-01")
        assert group.center_id == center.id

    def test_create_group_without_teacher_fails(self, api_client, director_user, center, course, room):
        api_client.force_authenticate(user=director_user)
        payload = {
            "name": "No Teacher Group",
            "course": str(course.id),
            "room": str(room.id),
            "status": "active",
            "start_date": date.today().isoformat(),
            "lesson_days": [0, 2, 4],
            "lesson_start_time": time(9, 0).isoformat(),
            "lesson_end_time": time(11, 0).isoformat(),
        }
        response = api_client.post("/api/v1/director/groups/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "teacher" in response.data

    def test_invalid_lesson_times_rejected(self, api_client, director_user, center, course, teacher, room):
        api_client.force_authenticate(user=director_user)
        payload = {
            "name": "Bad Times",
            "course": str(course.id),
            "teacher": str(teacher.id),
            "room": str(room.id),
            "status": "active",
            "start_date": date.today().isoformat(),
            "lesson_days": [0],
            "lesson_start_time": time(11, 0).isoformat(),
            "lesson_end_time": time(9, 0).isoformat(),
        }
        response = api_client.post("/api/v1/director/groups/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_only_shows_own_center_groups(
        self, api_client, director_user, center, other_center, course, teacher, room
    ):
        Group.objects.create(
            name="Mine",
            course=course,
            teacher=teacher,
            room=room,
            center=center,
            start_date=date.today(),
            lesson_days=[0],
            lesson_start_time=time(9, 0),
            lesson_end_time=time(10, 0),
        )
        other_course = Course.objects.create(name="Other", duration_months=1, price="100", center=other_center)
        other_teacher_user = User.objects.create_user(
            phone="998903333333", first_name="Other", last_name="Teacher", role=User.Role.TEACHER
        )
        other_teacher = Teacher.objects.create(user=other_teacher_user, centers=other_center)
        Group.objects.create(
            name="Not Mine",
            course=other_course,
            teacher=other_teacher,
            center=other_center,
            start_date=date.today(),
            lesson_days=[0],
            lesson_start_time=time(9, 0),
            lesson_end_time=time(10, 0),
        )

        api_client.force_authenticate(user=director_user)
        response = api_client.get("/api/v1/director/groups/")

        assert response.status_code == status.HTTP_200_OK
        names = [g["name"] for g in response.data.get("results", response.data)]
        assert "Mine" in names
        assert "Not Mine" not in names


@pytest.mark.django_db
class TestDirectorLessonCreate:
    def test_create_lesson_sets_group(self, api_client, director_user, group):
        api_client.force_authenticate(user=director_user)
        payload = {
            "group": str(group.id),
            "date": date.today().isoformat(),
            "start_time": time(9, 0).isoformat(),
            "end_time": time(10, 30).isoformat(),
            "topic": "React Hooks",
        }
        response = api_client.post("/api/v1/director/lessons/", payload)

        assert response.status_code == status.HTTP_201_CREATED, response.data
        lesson = Lesson.objects.get(topic="React Hooks")
        assert lesson.group_id == group.id


@pytest.mark.django_db
class TestDirectorAttendanceView:
    def test_mark_attendance_for_own_student(self, api_client, director_user, lesson, student_in_center):
        api_client.force_authenticate(user=director_user)
        payload = {"records": [{"student": str(student_in_center.id), "status": "present"}]}
        response = api_client.post(f"/api/v1/director/lessons/{lesson.id}/attendance/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert Attendance.objects.filter(lesson=lesson, student=student_in_center).exists()

    def test_mark_attendance_for_foreign_student_should_be_rejected(
        self, api_client, director_user, lesson, student_in_other_center
    ):
        api_client.force_authenticate(user=director_user)
        payload = {"records": [{"student": str(student_in_other_center.id), "status": "present"}]}
        response = api_client.post(f"/api/v1/director/lessons/{lesson.id}/attendance/", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Attendance.objects.filter(lesson=lesson, student=student_in_other_center).exists()
