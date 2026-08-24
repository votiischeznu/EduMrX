from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.models import (
    Attendance,
    Branch,
    Center,
    Debt,
    Group,
    Lesson,
    Payment,
    Student,
    Teacher,
)
from apps.models.payments import Expense
from apps.service.director_finance_service import DirectorFinanceService

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────


def money(value) -> str:
    """
    Barcha pul qiymatlarini boshqa modullar (PaymentListSerializer va h.k.)
    bilan izchil bo'lishi uchun string qilib qaytaradi, masalan '45000000.00'.
    None, int, float, Decimal — barchasini xavfsiz qabul qiladi.
    """
    if value is None:
        value = Decimal("0")
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            value = Decimal("0")
    return str(value.quantize(Decimal("0.01")))


def percent_change(current, previous) -> float:
    """Ikki qiymat orasidagi % o'zgarishni xavfsiz hisoblaydi (0 ga bo'lishdan himoyalangan)."""
    try:
        current = float(current or 0)
        previous = float(previous or 0)
    except (TypeError, ValueError):
        return 0.0

    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def get_director_centers(user):
    return Center.objects.filter(director=user)


def get_single_center_or_404(user):
    center = get_director_centers(user).first()
    if not center:
        raise NotFound("Sizga biriktirilgan markaz topilmadi.")
    return center


def get_period_range(period: str):
    """Berilgan period nomiga mos (start, end) datetime oralig'ini qaytaradi."""
    now = timezone.now()

    if period == "last_month":
        end = now.replace(day=1) - timedelta(microseconds=1)
        start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "3months":
        start = now - timedelta(days=90)
        end = now
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:  # "this_month" yoki noma'lum qiymat — default
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now

    return start, end


def get_previous_period_range(start, end):
    """Joriy davr bilan bir xil uzunlikdagi, undan oldingi davrni qaytaradi (solishtirish uchun)."""
    duration = end - start
    prev_end = start - timedelta(microseconds=1)
    prev_start = prev_end - duration
    return prev_start, prev_end


# ─────────────────────────────────────────────
# QUERYSET HELPERLAR (center + branch filtri)
# ─────────────────────────────────────────────


def _student_qs(centers, branch):
    qs = Student.objects.filter(center__in=centers, user__is_deleted=False)
    if branch:
        qs = qs.filter(branch=branch)
    return qs


def _group_qs(centers, branch):
    qs = Group.objects.filter(center__in=centers)
    if branch:
        qs = qs.filter(branch=branch)
    return qs


def _payment_qs(centers, branch):
    qs = Payment.objects.filter(student__center__in=centers)
    if branch:
        qs = qs.filter(branch=branch)
    return qs


def _debt_qs(centers, branch):
    qs = Debt.objects.filter(student__center__in=centers)
    if branch:
        qs = qs.filter(student__branch=branch)
    return qs


def _teacher_qs(centers, branch):
    qs = Teacher.objects.filter(centers__in=centers, user__is_deleted=False)
    if branch:
        qs = qs.filter(branch=branch)
    return qs.distinct()


# ─────────────────────────────────────────────
# DASHBOARD BO'LIMLARI
# ─────────────────────────────────────────────


def get_payment_status(centers, branch, start, end):
    payments = _payment_qs(centers, branch).filter(paid_at__range=(start, end))
    paid = payments.filter(status=Payment.Status.PAID).aggregate(t=Sum("final_amount"))["t"] or Decimal("0")
    pending = payments.filter(status=Payment.Status.PENDING).aggregate(t=Sum("final_amount"))["t"] or Decimal("0")

    debt = _debt_qs(centers, branch).filter(status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID]).aggregate(
        t=Sum("amount")
    )["t"] or Decimal("0")

    return {
        "paid": money(paid),
        "pending": money(pending),
        "debt": money(debt),
    }


def get_finance_chart(centers, branch, period="this_month"):
    """Oylik revenue/expense/profit. 'year' period bo'lsa 12 oy, aks holda 6 oy ko'rsatiladi."""
    months_back = 12 if period == "year" else 6

    now = timezone.now()
    range_start = (now.replace(day=1) - timedelta(days=31 * (months_back - 1))).replace(day=1)

    payments = _payment_qs(centers, branch).filter(status=Payment.Status.PAID, paid_at__gte=range_start)
    revenue_rows = (
        payments.annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(total=Sum("final_amount", output_field=DecimalField()))
    )
    revenue_map = {r["month"].strftime("%Y-%m"): r["total"] for r in revenue_rows if r["month"]}

    expense_qs = Expense.objects.filter(
        center__in=centers,
        status=Expense.Status.PAID,
        expense_date__gte=range_start.date(),
    )
    if branch:
        expense_qs = expense_qs.filter(branch=branch)
    expense_rows = (
        expense_qs.annotate(month=TruncMonth("expense_date"))
        .values("month")
        .annotate(total=Sum("amount", output_field=DecimalField()))
    )
    expense_map = {e["month"].strftime("%Y-%m"): e["total"] for e in expense_rows if e["month"]}

    months_uz = ["Yan", "Fev", "Mar", "Apr", "May", "Iyn", "Iyl", "Avg", "Sen", "Okt", "Noy", "Dek"]
    chart = []
    cursor = range_start
    for _ in range(months_back):
        key = cursor.strftime("%Y-%m")
        revenue = revenue_map.get(key) or Decimal("0")
        expense = expense_map.get(key) or Decimal("0")
        chart.append(
            {
                "month": months_uz[cursor.month - 1],
                "revenue": money(revenue),
                "expense": money(expense),
                "profit": money(revenue - expense),
            }
        )
        # keyingi oyning 1-sanasiga o'tish (oy uzunligidan qat'iy nazar xavfsiz usul)
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    return chart


def get_today_lessons(centers, branch):
    today = timezone.localdate()
    qs = Lesson.objects.select_related("group", "group__teacher", "group__teacher__user", "group__room").filter(
        group__center__in=centers, date=today
    )
    if branch:
        qs = qs.filter(group__branch=branch)
    qs = qs.order_by("start_time")

    return [
        {
            "id": str(lesson.id),
            "group_name": lesson.group.name,
            "time": lesson.start_time.strftime("%H:%M"),
            "teacher_name": lesson.group.teacher.full_name if lesson.group.teacher_id else None,
            "room_name": lesson.group.room.name if lesson.group.room_id else None,
        }
        for lesson in qs
    ]


def get_recent_payments(centers, branch, limit=5):
    qs = (
        _payment_qs(centers, branch)
        .filter(status=Payment.Status.PAID)
        .select_related("student__user")
        .order_by("-paid_at")[:limit]
    )

    return [
        {
            "student_name": p.student.full_name,
            "amount": money(p.final_amount),
            "paid_at": p.paid_at,
            "status": p.status,
        }
        for p in qs
    ]


def get_top_debtors(centers, branch, limit=5):
    qs = (
        _debt_qs(centers, branch)
        .filter(status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID])
        .select_related("student__user")
        .order_by("-amount")[:limit]
    )

    return [
        {
            "student_name": d.student.full_name,
            "student_phone": d.student.phone,
            "amount": money(d.amount),
            "due_date": d.due_date,
        }
        for d in qs
    ]


def get_branches_status(centers, start):
    """
    N+1 query'siz — bitta annotate orqali barcha filiallarning
    o'quvchilar soni va oylik daromadini hisoblaydi.
    """
    branches = Branch.objects.filter(center__in=centers).annotate(
        students_total=Count(
            "students",
            filter=Q_students_active(),
            distinct=True,
        ),
    )

    result = []
    for b in branches:
        month_revenue = Payment.objects.filter(branch=b, status=Payment.Status.PAID, paid_at__gte=start).aggregate(
            t=Sum("final_amount")
        )["t"] or Decimal("0")

        result.append(
            {
                "id": str(b.id),
                "name": b.name,
                "students_count": b.students_total,
                "month_revenue": money(month_revenue),
                "status": b.status,
            }
        )
    return result


def Q_students_active():
    """Branch.students Count uchun faqat o'chirilmagan foydalanuvchilarni hisoblash filtri."""
    from django.db.models import Q

    return Q(students__user__is_deleted=False)


def get_quick_stats(centers, branch, start, end):
    students = _student_qs(centers, branch)
    new_students = students.filter(created_at__range=(start, end)).count()

    groups = _group_qs(centers, branch)
    active_groups_qs = groups.filter(status=Group.Status.ACTIVE)
    active_groups = active_groups_qs.count()

    teachers_count = _teacher_qs(centers, branch).count()

    filled = (
        active_groups_qs
        .select_related("room")
        .exclude(room__isnull=True)
        .annotate(_sc=Count("enrollments", distinct=True))
    )
    rates = [(g._sc / g.room.capacity) * 100 for g in filled if g.room.capacity]
    avg_fill_rate = round(sum(rates) / len(rates), 1) if rates else 0.0

    return {
        "new_students": new_students,
        "active_groups": active_groups,
        "teachers_count": teachers_count,
        "avg_fill_rate": avg_fill_rate,
    }


def get_attendance_avg(centers, branch, start, end):
    qs = Attendance.objects.filter(
        lesson__group__center__in=centers,
        lesson__date__range=(start.date(), end.date()),
    )
    if branch:
        qs = qs.filter(lesson__group__branch=branch)

    total = qs.count()
    if not total:
        return 0.0
    present = qs.filter(status=Attendance.Status.PRESENT).count()
    return round((present / total) * 100, 1)


def get_students_change(centers, branch, start, end):
    """
    Joriy davrda qo'shilgan yangi o'quvchilar soni asosida taxminiy % o'sish.
    (To'liq tarixiy snapshot bo'lmagani uchun yaqinlashtirilgan hisob-kitob.)
    """
    students = _student_qs(centers, branch)
    current_total = students.filter(status=Student.Status.ACTIVE).count()
    new_in_period = students.filter(created_at__range=(start, end)).count()
    previous_total = max(current_total - new_in_period, 0)
    return percent_change(current_total, previous_total)


def get_attendance_change(centers, branch, start, end):
    """Joriy davr bilan bir xil uzunlikdagi oldingi davr davomidagi davomat farqi (foiz punktda)."""
    prev_start, prev_end = get_previous_period_range(start, end)
    current_avg = get_attendance_avg(centers, branch, start, end)
    previous_avg = get_attendance_avg(centers, branch, prev_start, prev_end)
    return round(current_avg - previous_avg, 1)


# ─────────────────────────────────────────────
# ASOSIY YIG'UVCHI FUNKSIYA
# ─────────────────────────────────────────────


def get_dashboard_data_from_centers(centers, branch, period="this_month"):
    """
    centers — director'ga tegishli Center queryset (DirectorAnalyticsBaseView.get_centers_and_branch dan).
    branch  — Branch instance yoki None (None bo'lsa — butun markaz bo'yicha).
    period  — this_month / last_month / 3months / year.
    """
    if not centers.exists():
        raise NotFound("Sizga biriktirilgan markaz topilmadi.")

    start, end = get_period_range(period)

    finance_summary = DirectorFinanceService.get_summary_data(centers, branch=branch)

    students_qs = _student_qs(centers, branch)
    active_students = students_qs.filter(status=Student.Status.ACTIVE).count()

    kpi = {
        "students_count": active_students,
        "students_change": get_students_change(centers, branch, start, end),
        "month_revenue": money(finance_summary.get("month_revenue")),
        "revenue_change": finance_summary.get("month_revenue_change", 0),
        "pending_debts": money(finance_summary.get("pending_debts")),
        "debtors_count": finance_summary.get("pending_debts_students_count", 0),
        "attendance_avg": get_attendance_avg(centers, branch, start, end),
        "attendance_change": get_attendance_change(centers, branch, start, end),
    }

    return {
        "kpi": kpi,
        "finance_chart": get_finance_chart(centers, branch, period=period),
        "payment_status": get_payment_status(centers, branch, start, end),
        "today_lessons": get_today_lessons(centers, branch),
        "recent_payments": get_recent_payments(centers, branch),
        "top_debtors": get_top_debtors(centers, branch),
        "branches_status": get_branches_status(centers, start) if not branch else [],
        "quick_stats": get_quick_stats(centers, branch, start, end),
    }
