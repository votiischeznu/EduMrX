"""
Manager Dashboard, Student, Teacher, Room, Course, Group, Lesson,
Attendance va Payment endpointlari uchun testlar.

Ishga tushirish:
    pytest apps/tests/test_manager_views.py -v

MUHIM ESLATMA:
    Loyihada alohida "Manager" roli yo'q -- `get_manager_branch_or_404`
    `request.user.staff_profile` (bu `CenterStaff.user`ning related_name'i,
    faqat `User.Role.ADMIN` bilan bog'lanadi) orqali center/branch'ni oladi.
    Shu sababli manager foydalanuvchilari `role=User.Role.ADMIN` bilan
    yaratiladi va `CenterStaff` orqali center/branch'ga biriktiriladi.
    `IsManager` permission ham role == ADMIN'ni tekshiradi deb faraz
    qilindi -- agar boshqacha logika bo'lsa, shunga qarab moslashtiring.
"""

from datetime import date, time

import pytest
from django.urls import reverse
from rest_framework import status

from apps.models import (
    Branch,
    Center,
    CenterStaff,
    Course,
    Group,
    GroupStudent,
    Lesson,
    Payment,
    Room,
    Student,
    Teacher,
    User,
)

# ===========================================================================
# Asosiy tashkilot: Center / Branch qo'shimchalari
# (api_client, director_user, center, branch, course, teacher_user, lesson
# fixture'lari conftest.py'dan keladi)
# ===========================================================================


@pytest.fixture
def other_center(director_user):
    """Manager tegishli bo'lmagan boshqa markaz."""
    return Center.objects.create(
        name="Boshqa Markaz",
        slug="boshqa-markaz",
        director=director_user,
    )


@pytest.fixture
def other_branch(center):
    """Bir markazdagi, lekin manager biriktirilmagan boshqa filial."""
    return Branch.objects.create(name="Ikkinchi filial", center=center, latitude=0.0, longitude=0.0)


# ===========================================================================
# Manager foydalanuvchisi
# ===========================================================================


@pytest.fixture
def manager_user():
    user = User.objects.create_user(
        phone="998900000001",
        first_name="Manager",
        last_name="Boshqaruvchi",
        role=User.Role.ADMIN,
        is_active=True,
    )
    user.set_password("123m")
    user.save()
    return user


@pytest.fixture
def manager_staff(manager_user, center, branch):
    """Manager'ni (ADMIN rolidagi user) center va branch'ga biriktiradi."""
    return CenterStaff.objects.create(user=manager_user, center=center, branch=branch)


@pytest.fixture
def manager_without_branch():
    """Filialga biriktirilmagan manager (staff_profile.branch_id yo'q)."""
    user = User.objects.create_user(
        phone="998900000002",
        first_name="Filialsiz",
        last_name="Manager",
        role=User.Role.ADMIN,
        is_active=True,
    )
    user.set_password("123m")
    user.save()
    return user


@pytest.fixture
def manager_without_profile():
    """staff_profile umuman mavjud bo'lmagan manager."""
    user = User.objects.create_user(
        phone="998900000003",
        first_name="Profilsiz",
        last_name="Manager",
        role=User.Role.ADMIN,
        is_active=True,
    )
    user.set_password("123m")
    user.save()
    return user


# ===========================================================================
# Domen fixture'lari (bu faylga xos: branch'ni hisobga oladi)
# ===========================================================================


@pytest.fixture
def room(center, branch):
    return Room.objects.create(center=center, branch=branch, name="101", capacity=20)


@pytest.fixture
def teacher(teacher_user, center, branch):
    return Teacher.objects.create(user=teacher_user, centers=center, branch=branch)


@pytest.fixture
def group(center, branch, course, teacher, room):
    return Group.objects.create(
        name="Frontend-01",
        course=course,
        teacher=teacher,
        room=room,
        center=center,
        branch=branch,
        start_date=date.today(),
        lesson_days=[0],
        lesson_start_time=time(9, 0),
        lesson_end_time=time(10, 0),
    )


@pytest.fixture
def student_in_branch(center, branch):
    user = User.objects.create_user(
        phone="998903333333",
        first_name="Ali",
        last_name="Student",
        role=User.Role.STUDENT,
    )
    return Student.objects.create(user=user, center=center, branch=branch)


@pytest.fixture
def student_in_other_branch(center, other_branch):
    """Bir markazda, lekin manager filialiga tegishli bo'lmagan student."""
    user = User.objects.create_user(
        phone="998904444444",
        first_name="Boshqa",
        last_name="Filial",
        role=User.Role.STUDENT,
    )
    return Student.objects.create(user=user, center=center, branch=other_branch)


@pytest.fixture
def payment(student_in_branch, branch):
    today = date.today()
    return Payment.objects.create(
        student=student_in_branch,
        branch=branch,
        amount="500000",
        discount="0",
        final_amount="500000",
        due_date=today,
        period_month=today.month,
        period_year=today.year,
        receipt_number="TEST-0001",
    )


# ===========================================================================
# DASHBOARD
# ===========================================================================


@pytest.mark.django_db
class TestManagerDashboard:
    def test_dashboard_success(self, api_client, manager_user, manager_staff, student_in_branch, teacher, group):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-dashboard"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["center"]["id"] == manager_staff.center.id
        assert response.data["branch"]["id"] == manager_staff.branch.id
        assert response.data["statistics"]["total_students"] >= 1
        assert response.data["statistics"]["total_teachers"] >= 1
        assert response.data["statistics"]["total_groups"] >= 1
        assert "finance_this_month" in response.data

    def test_dashboard_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse("manager-dashboard"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_no_staff_profile_returns_404(self, api_client, manager_without_profile):
        api_client.force_authenticate(user=manager_without_profile)
        response = api_client.get(reverse("manager-dashboard"))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_dashboard_no_branch_returns_404(self, api_client, manager_without_branch, center):
        CenterStaff.objects.create(user=manager_without_branch, center=center, branch=None)
        api_client.force_authenticate(user=manager_without_branch)
        response = api_client.get(reverse("manager-dashboard"))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_director_role_forbidden(self, api_client, director_user):
        """IsManager permission direktorga ruxsat bermasligi kerak."""
        api_client.force_authenticate(user=director_user)
        response = api_client.get(reverse("manager-dashboard"))
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ===========================================================================
# STUDENTS
# ===========================================================================


@pytest.mark.django_db
class TestManagerStudentList:
    def test_list_own_branch_students(self, api_client, manager_user, manager_staff, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-students-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [s["id"] for s in response.data["results"]]
        assert str(student_in_branch.id) in ids

    def test_other_branch_student_not_visible(self, api_client, manager_user, manager_staff, student_in_other_branch):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-students-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [s["id"] for s in response.data["results"]]
        assert str(student_in_other_branch.id) not in ids

    def test_search_by_first_name(self, api_client, manager_user, manager_staff, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(
            reverse("manager-students-list-create"), {"search": student_in_branch.user.first_name}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse("manager-students-list-create"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestManagerStudentCreate:
    def test_create_student_success(self, api_client, manager_user, manager_staff):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "phone": "998909998877",
            "first_name": "Yangi",
            "last_name": "Student",
            "status": "active",
        }
        response = api_client.post(reverse("manager-students-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        student = Student.objects.get(user__phone="998909998877")
        assert student.center_id == manager_staff.center_id
        assert student.branch_id == manager_staff.branch_id

    def test_create_student_duplicate_phone_fails(self, api_client, manager_user, manager_staff, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "phone": student_in_branch.user.phone,
            "first_name": "Test",
            "last_name": "Test",
        }
        response = api_client.post(reverse("manager-students-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data

    def test_create_student_missing_phone_fails(self, api_client, manager_user, manager_staff):
        api_client.force_authenticate(user=manager_user)
        payload = {"first_name": "Test", "last_name": "Test"}
        response = api_client.post(reverse("manager-students-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data


@pytest.mark.django_db
class TestManagerStudentDetail:
    def test_retrieve_student(self, api_client, manager_user, manager_staff, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-students-detail", kwargs={"pk": student_in_branch.id}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(student_in_branch.id)

    def test_retrieve_other_branch_student_returns_404(
        self, api_client, manager_user, manager_staff, student_in_other_branch
    ):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-students-detail", kwargs={"pk": student_in_other_branch.id}))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_student_first_name(self, api_client, manager_user, manager_staff, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        payload = {"first_name": "Yangilangan"}
        response = api_client.patch(
            reverse("manager-students-detail", kwargs={"pk": student_in_branch.id}), payload, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        student_in_branch.user.refresh_from_db()
        assert student_in_branch.user.first_name == "Yangilangan"

    def test_soft_delete_student(self, api_client, manager_user, manager_staff, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        response = api_client.delete(reverse("manager-students-detail", kwargs={"pk": student_in_branch.id}))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        student_in_branch.user.refresh_from_db()
        assert student_in_branch.user.is_deleted is True
        assert student_in_branch.user.is_active is False

    def test_deleted_student_not_in_list(self, api_client, manager_user, manager_staff, student_in_branch):
        student_in_branch.user.is_deleted = True
        student_in_branch.user.is_active = False
        student_in_branch.user.save()

        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-students-list-create"))
        ids = [s["id"] for s in response.data["results"]]
        assert str(student_in_branch.id) not in ids

    def test_put_method_not_allowed(self, api_client, manager_user, manager_staff, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        response = api_client.put(
            reverse("manager-students-detail", kwargs={"pk": student_in_branch.id}), {}, format="json"
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ===========================================================================
# TEACHERS
# ===========================================================================


@pytest.mark.django_db
class TestManagerTeacherList:
    def test_list_own_branch_teachers(self, api_client, manager_user, manager_staff, teacher):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-teachers-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [t["id"] for t in response.data["results"]]
        assert str(teacher.id) in ids

    def test_other_branch_teacher_not_visible(self, api_client, manager_user, manager_staff, center, other_branch):
        other_user = User.objects.create_user(phone="998906666666", role=User.Role.TEACHER)
        other_teacher = Teacher.objects.create(user=other_user, centers=center, branch=other_branch)

        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-teachers-list-create"))
        ids = [t["id"] for t in response.data["results"]]
        assert str(other_teacher.id) not in ids


@pytest.mark.django_db
class TestManagerTeacherCreate:
    def test_create_teacher_success(self, api_client, manager_user, manager_staff):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "phone": "998901234567",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "password": "securepassword",
            "salary": "1000000.00",
            "experience": 3,
            "specialization": "Backend",
        }
        response = api_client.post(reverse("manager-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        teacher = Teacher.objects.get(user__first_name="Ali")
        assert teacher.centers.id == manager_staff.center.id
        assert teacher.branch_id == manager_staff.branch_id

    def test_create_teacher_without_password_sets_temp_password(self, api_client, manager_user, manager_staff):
        """
        ManagerTeacherCreateSerializer'da `password` majburiy emas (required=False).
        Berilmasa, avtomatik vaqtinchalik parol yaratiladi va
        user.must_change_password=True qilib qo'yiladi.
        """
        api_client.force_authenticate(user=manager_user)
        payload = {"phone": "998901234568", "first_name": "Ali", "last_name": "Valiyev"}
        response = api_client.post(reverse("manager-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        teacher = Teacher.objects.get(user__phone="998901234568")
        assert teacher.user.must_change_password is True

    def test_create_teacher_duplicate_phone_fails(self, api_client, manager_user, manager_staff, teacher):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "phone": teacher.user.phone,
            "first_name": "Yangi",
            "last_name": "Teacher",
            "password": "password123",
        }
        response = api_client.post(reverse("manager-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data

    def test_create_teacher_duplicate_email_fails(self, api_client, manager_user, manager_staff, teacher_user):
        teacher_user.email = "existing@example.com"
        teacher_user.save(update_fields=["email"])

        api_client.force_authenticate(user=manager_user)
        payload = {
            "phone": "998901234569",
            "first_name": "Yangi",
            "last_name": "Teacher",
            "email": "EXISTING@example.com",
        }
        response = api_client.post(reverse("manager-teachers-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data


@pytest.mark.django_db
class TestManagerTeacherDetail:
    def test_retrieve_teacher(self, api_client, manager_user, manager_staff, teacher):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-teachers-detail", kwargs={"pk": teacher.id}))
        assert response.status_code == status.HTTP_200_OK

    def test_soft_delete_teacher(self, api_client, manager_user, manager_staff, teacher):
        api_client.force_authenticate(user=manager_user)
        response = api_client.delete(reverse("manager-teachers-detail", kwargs={"pk": teacher.id}))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        teacher.user.refresh_from_db()
        assert teacher.user.is_deleted is True


# ===========================================================================
# ROOMS
# ===========================================================================


@pytest.mark.django_db
class TestManagerRoom:
    def test_list_rooms(self, api_client, manager_user, manager_staff, room):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-rooms-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert str(room.id) in ids

    def test_create_room(self, api_client, manager_user, manager_staff):
        api_client.force_authenticate(user=manager_user)
        payload = {"name": "202", "capacity": 15}
        response = api_client.post(reverse("manager-rooms-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Room.objects.filter(name="202", center=manager_staff.center, branch=manager_staff.branch).exists()

    def test_other_branch_room_not_accessible(self, api_client, manager_user, manager_staff, center, other_branch):
        other_room = Room.objects.create(center=center, branch=other_branch, name="303", capacity=10)
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-rooms-detail", kwargs={"pk": other_room.id}))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ===========================================================================
# COURSES
# ===========================================================================


@pytest.mark.django_db
class TestManagerCourse:
    def test_list_courses(self, api_client, manager_user, manager_staff, course):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-courses-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [c["id"] for c in response.data["results"]]
        assert str(course.id) in ids

    def test_create_course(self, api_client, manager_user, manager_staff):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "name": "Backend",
            "duration_months": 6,
            "price": "1500000",
            "status": "active",
        }
        response = api_client.post(reverse("manager-courses-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Course.objects.filter(name="Backend", center=manager_staff.center).exists()

    def test_other_center_course_not_accessible(self, api_client, manager_user, manager_staff, other_center):
        other_course = Course.objects.create(
            name="Other", duration_months=6, price="1500000", status=Course.Status.ACTIVE, center=other_center
        )
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-courses-detail", kwargs={"pk": other_course.id}))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ===========================================================================
# GROUPS
# ===========================================================================


@pytest.mark.django_db
class TestManagerGroupList:
    def test_list_own_branch_groups(self, api_client, manager_user, manager_staff, group):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-groups-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [g["id"] for g in response.data["results"]]
        assert str(group.id) in ids


@pytest.mark.django_db
class TestManagerGroupCreate:
    def test_create_group_success(self, api_client, manager_user, manager_staff, course, teacher, room):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "name": "Backend-01",
            "course": str(course.id),
            "teacher": str(teacher.id),
            "room": str(room.id),
            "start_date": str(date.today()),
            "lesson_days": [1, 3],
            "lesson_start_time": "10:00:00",
            "lesson_end_time": "11:00:00",
        }
        response = api_client.post(reverse("manager-groups-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        group = Group.objects.get(name="Backend-01")
        assert group.center_id == manager_staff.center_id
        assert group.branch_id == manager_staff.branch_id


@pytest.mark.django_db
class TestManagerGroupDetail:
    def test_update_group_partial(self, api_client, manager_user, manager_staff, group):
        api_client.force_authenticate(user=manager_user)
        payload = {"name": "Frontend-02"}
        response = api_client.patch(reverse("manager-groups-detail", kwargs={"pk": group.id}), payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        group.refresh_from_db()
        assert group.name == "Frontend-02"

    def test_update_group_full_payload(self, api_client, manager_user, manager_staff, group, course, teacher, room):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "name": "Frontend-02",
            "course": str(course.id),
            "teacher": str(teacher.id),
            "room": str(room.id),
            "start_date": str(date.today()),
            "lesson_days": [0],
            "lesson_start_time": "09:00:00",
            "lesson_end_time": "10:00:00",
        }
        response = api_client.patch(reverse("manager-groups-detail", kwargs={"pk": group.id}), payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        group.refresh_from_db()
        assert group.name == "Frontend-02"

    def test_other_branch_group_returns_404(
        self, api_client, manager_user, manager_staff, center, other_branch, course, teacher
    ):
        other_room = Room.objects.create(center=center, branch=other_branch, name="X", capacity=10)
        other_group = Group.objects.create(
            name="Other-Group",
            course=course,
            teacher=teacher,
            room=other_room,
            center=center,
            branch=other_branch,
            start_date=date.today(),
            lesson_days=[0],
            lesson_start_time=time(9, 0),
            lesson_end_time=time(10, 0),
        )
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-groups-detail", kwargs={"pk": other_group.id}))
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestManagerGroupEnroll:
    def test_enroll_student_success(self, api_client, manager_user, manager_staff, group, student_in_branch):
        api_client.force_authenticate(user=manager_user)
        payload = {"student_id": str(student_in_branch.id), "action": "add"}
        response = api_client.post(reverse("manager-groups-enroll", kwargs={"pk": group.id}), payload, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_enroll_group_not_found_for_other_branch(
        self, api_client, manager_user, manager_staff, center, other_branch, course, teacher
    ):
        other_room = Room.objects.create(center=center, branch=other_branch, name="Y", capacity=10)
        other_group = Group.objects.create(
            name="Other-Group-2",
            course=course,
            teacher=teacher,
            room=other_room,
            center=center,
            branch=other_branch,
            start_date=date.today(),
            lesson_days=[0],
            lesson_start_time=time(9, 0),
            lesson_end_time=time(10, 0),
        )
        api_client.force_authenticate(user=manager_user)
        response = api_client.post(reverse("manager-groups-enroll", kwargs={"pk": other_group.id}), {}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ===========================================================================
# LESSONS
# ===========================================================================


@pytest.mark.django_db
class TestManagerLessonList:
    def test_list_own_branch_lessons(self, api_client, manager_user, manager_staff, lesson):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-lessons-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [item["id"] for item in response.data["results"]]
        assert str(lesson.id) in ids


@pytest.mark.django_db
class TestManagerLessonCreate:
    def test_create_lesson_success(self, api_client, manager_user, manager_staff, group):
        api_client.force_authenticate(user=manager_user)
        payload = {
            "group": str(group.id),
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        }
        response = api_client.post(reverse("manager-lessons-list-create"), payload, format="json")
        print("DEBUG:", response.status_code, response.data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_lesson_other_branch_group_forbidden(
        self, api_client, manager_user, manager_staff, center, other_branch, course, teacher
    ):
        other_room = Room.objects.create(center=center, branch=other_branch, name="Z", capacity=10)
        other_group = Group.objects.create(
            name="Other-Group-3",
            course=course,
            teacher=teacher,
            room=other_room,
            center=center,
            branch=other_branch,
            start_date=date.today(),
            lesson_days=[0],
            lesson_start_time=time(9, 0),
            lesson_end_time=time(10, 0),
        )
        api_client.force_authenticate(user=manager_user)
        payload = {
            "group": str(other_group.id),
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        }
        response = api_client.post(reverse("manager-lessons-list-create"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestManagerLessonDetail:
    def test_retrieve_lesson(self, api_client, manager_user, manager_staff, lesson):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-lessons-detail", kwargs={"pk": lesson.id}))
        assert response.status_code == status.HTTP_200_OK


# ===========================================================================
# ATTENDANCE
# ===========================================================================


@pytest.mark.django_db
class TestManagerAttendance:
    def test_get_attendance_list(self, api_client, manager_user, manager_staff, lesson):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-lessons-attendance", kwargs={"pk": lesson.id}))
        assert response.status_code == status.HTTP_200_OK

    def test_post_attendance_bulk(self, api_client, manager_user, manager_staff, lesson, group, student_in_branch):
        GroupStudent.objects.create(group=group, student=student_in_branch)
        api_client.force_authenticate(user=manager_user)
        payload = {
            "records": [
                {"student": str(student_in_branch.id), "status": "present"},
            ]
        }
        response = api_client.post(
            reverse("manager-lessons-attendance", kwargs={"pk": lesson.id}), payload, format="json"
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_attendance_other_branch_lesson_404(
        self, api_client, manager_user, manager_staff, center, other_branch, course, teacher
    ):
        other_room = Room.objects.create(center=center, branch=other_branch, name="W", capacity=10)
        other_group = Group.objects.create(
            name="Other-Group-4",
            course=course,
            teacher=teacher,
            room=other_room,
            center=center,
            branch=other_branch,
            start_date=date.today(),
            lesson_days=[0],
            lesson_start_time=time(9, 0),
            lesson_end_time=time(10, 0),
        )
        other_lesson = Lesson.objects.create(
            group=other_group, date=date.today(), start_time=time(9, 0), end_time=time(10, 0)
        )
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-lessons-attendance", kwargs={"pk": other_lesson.id}))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ===========================================================================
# PAYMENTS
# ===========================================================================


@pytest.mark.django_db
class TestManagerPaymentList:
    def test_list_own_branch_payments(self, api_client, manager_user, manager_staff, payment):
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-payments-list-create"))
        assert response.status_code == status.HTTP_200_OK
        ids = [p["id"] for p in response.data["results"]]
        assert str(payment.id) in ids

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse("manager-payments-list-create"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_other_branch_payment_not_visible(
        self, api_client, manager_user, manager_staff, center, other_branch, student_in_other_branch
    ):
        today = date.today()
        other_payment = Payment.objects.create(
            student=student_in_other_branch,
            branch=other_branch,
            amount="300000",
            discount="0",
            final_amount="300000",
            due_date=today,
            period_month=today.month,
            period_year=today.year,
            receipt_number="TEST-0002",
        )
        api_client.force_authenticate(user=manager_user)
        response = api_client.get(reverse("manager-payments-list-create"))
        ids = [p["id"] for p in response.data["results"]]
        assert str(other_payment.id) not in ids
