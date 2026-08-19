from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.models import (
    Branch,
    Center,
    CenterStaff,
    Course,
    Debt,
    Group,
    Notification,
    Parent,
    Payment,
    Room,
    Student,
    Teacher,
    User,
)


class Command(BaseCommand):
    help = "Seed database with initial data"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Seeding database...")

            # 1. User
            user_admin = User.objects.create_user(
                phone="+998901234567",
                password="password123",
                first_name="Admin",
                last_name="User",
                role=User.Role.SUPER_ADMIN,
            )
            user_director = User.objects.create_user(
                phone="+998901234570",
                password="password123",
                first_name="Director",
                last_name="User",
                role=User.Role.DIRECTOR,
            )
            user_manager = User.objects.create_user(
                phone="+998901234571",
                password="password123",
                first_name="Manager",
                last_name="User",
                role=User.Role.ADMIN,
            )
            user_teacher = User.objects.create_user(
                phone="+998901234568",
                password="password123",
                first_name="Teacher",
                last_name="One",
                role=User.Role.TEACHER,
            )
            user_student = User.objects.create_user(
                phone="+998901234569",
                password="password123",
                first_name="Student",
                last_name="One",
                role=User.Role.STUDENT,
            )
            user_parent = User.objects.create_user(
                phone="+998901234572",
                password="password123",
                first_name="Parent",
                last_name="User",
                role=User.Role.PARENT,
            )

            # 2. Center
            center = Center.objects.create(name="EduCenter", director=user_director)
            branch = Branch.objects.create(
                center=center,
                name="Branch A",
                address="Tashkent City",
                phone="+998901234500",
                latitude=41.2995,
                longitude=69.2401,
            )

            # 2.5 CenterStaff (Manager)
            CenterStaff.objects.create(user=user_manager, center=center, branch=branch)

            # 3. Course
            course = Course.objects.create(center=center, name="Python", price=Decimal("1000000.00"))

            # 4. Room
            room = Room.objects.create(center=center, branch=branch, name="Room 101", capacity=20)

            # 5. Teacher
            teacher = Teacher.objects.create(user=user_teacher)

            # 6. Group
            group = Group.objects.create(
                course=course,
                branch=branch,
                teacher=teacher,
                name="Python Group 1",
                room=room,
                start_date=timezone.now().date(),
                lesson_start_time=timezone.now().time(),
                lesson_end_time=timezone.now().time(),
            )

            # 7. Student/Parent
            student = Student.objects.create(user=user_student, center=center)
            parent = Parent.objects.create(user=user_parent)

            Payment.objects.create(
                student=student,
                amount=Decimal("100000.00"),
                final_amount=Decimal("100000.00"),
                period_month=8,
                period_year=2026,
                due_date=timezone.now().date(),
            )
            Debt.objects.create(
                student=student, group=group, amount=Decimal("50000.00"), due_date=timezone.now().date()
            )

            # 9. Notification
            Notification.objects.create(title="Welcome", body="Welcome to the center!")

            self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
