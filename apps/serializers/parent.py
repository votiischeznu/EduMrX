from django.utils import timezone
from rest_framework.fields import CharField, DateField, SerializerMethodField, UUIDField
from rest_framework.serializers import Serializer
from apps.models import Attendance, Group, Payment, Student

class ParentChildScheduleSerializer(Serializer):
    group_id = UUIDField(source="id", read_only=True)
    group_name = CharField(source="name", read_only=True)
    course_name = CharField(source="course.name", read_only=True)
    days = SerializerMethodField()
    start_time = SerializerMethodField()
    end_time = SerializerMethodField()

    def get_days(self, group):
        day_labels = dict(Group.DayOfWeek.choices)
        return [day_labels.get(day, str(day)) for day in group.lesson_days]

    def get_start_time(self, group):
        return group.lesson_start_time.strftime("%H:%M")

    def get_end_time(self, group):
        return group.lesson_end_time.strftime("%H:%M")

class ParentChildPaymentSerializer(Serializer):
    id = UUIDField(read_only=True)
    amount = SerializerMethodField()
    status = CharField(read_only=True)
    due_date = DateField(read_only=True)
    days_remaining = SerializerMethodField()
    is_overdue = SerializerMethodField()
    can_pay = SerializerMethodField()

    def get_amount(self, payment):
        return str(payment.final_amount)

    def get_days_remaining(self, payment):
        return (payment.due_date - timezone.now().date()).days

    def get_is_overdue(self, payment):
        return payment.due_date < timezone.now().date() and payment.status != Payment.Status.PAID

    def get_can_pay(self, payment):
        return payment.status in [Payment.Status.PENDING, Payment.Status.OVERDUE]

class ParentChildSerializer(Serializer):
    id = UUIDField(read_only=True)
    full_name = CharField(read_only=True)
    status = CharField(read_only=True)
    center_name = SerializerMethodField()
    schedules = SerializerMethodField()
    attendance_summary = SerializerMethodField()
    next_payment = SerializerMethodField()
    payments = SerializerMethodField()

    def get_center_name(self, student):
        return student.center.name if student.center_id else None

    def get_schedules(self, student):
        groups = Group.objects.filter(
            enrollments__student=student, enrollments__is_active=True
        ).select_related("course").distinct()
        return ParentChildScheduleSerializer(groups, many=True).data

    def get_attendance_summary(self, student):
        qs = Attendance.objects.filter(student=student)
        total = qs.count()
        present = qs.filter(status=Attendance.Status.PRESENT).count()
        return {
            "total_lessons": total,
            "present": present,
            "absent": total - present,
            "attendance_rate": round(present / total * 100, 1) if total else None,
        }

    def get_next_payment(self, student):
        payment = student.payments.filter(
            status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE]
        ).order_by("due_date").first()
        return ParentChildPaymentSerializer(payment).data if payment else None

    def get_payments(self, student):
        payments = student.payments.all().order_by("-due_date")
        return ParentChildPaymentSerializer(payments, many=True).data

class ParentDashboardSerializer(Serializer):
    id = UUIDField(read_only=True)
    full_name = CharField(read_only=True)
    phone = CharField(read_only=True)
    children = SerializerMethodField()

    def get_children(self, parent):
        children = parent.students.select_related("center").all()
        return ParentChildSerializer(children, many=True).data

class ParentPaymentInitiateSerializer(Serializer):
    payment_id = UUIDField()