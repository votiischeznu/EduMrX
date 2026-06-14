from rest_framework import serializers
from rest_framework.fields import (
    IntegerField,
    FloatField,
    BooleanField,
    CharField,
    DateTimeField,
)
from rest_framework.serializers import Serializer


class BaseCenterStatsSerializer(Serializer):
    active = IntegerField(help_text="Faol markazlar soni")
    total = IntegerField(help_text="Jami markazlar soni")


class BaseStudentStatsSerializer(Serializer):
    new_this_month = IntegerField(help_text="Shu oyda qo'shilgan yangi o'quvchilar")
    total = IntegerField(help_text="Jami o'quvchilar soni")


class BaseRevenueStatsSerializer(Serializer):
    total_this_month = IntegerField(help_text="Shu oydagi jami tushum")
    percentage_change = FloatField(help_text="O'tgan oyga nisbatan foizdagi farq")
    is_up = BooleanField(help_text="Tushum o'sganmi yoki kamayganmi")


class BaseSubscriptionStatsSerializer(Serializer):
    trial = IntegerField(help_text="Trial tarifidagi markazlar soni")
    pro = IntegerField(help_text="Pro tarifidagi markazlar soni")
    enterprise = IntegerField(help_text="Enterprise tarifidagi markazlar soni")
    total = IntegerField(help_text="Jami obunalar soni")


class BaseTicketStatsSerializer(Serializer):
    open = IntegerField(help_text="Ochiq ticketlar (ogohlantirishlar) soni")


class KPISerializer(Serializer):
    centers = BaseCenterStatsSerializer()
    students = BaseStudentStatsSerializer()
    revenue = BaseRevenueStatsSerializer()
    subscriptions = BaseSubscriptionStatsSerializer()
    tickets = BaseTicketStatsSerializer()


class Revenue12MSerializer(Serializer):
    month = CharField(help_text="Oy nomi (Masalan: 'Yan')")
    amount = IntegerField(help_text="Oylik tushum miqdori")


class StudentGrowthSerializer(Serializer):
    month = CharField(help_text="Oy nomi")
    count = IntegerField(help_text="O'sha oydagi jami kumulyativ o'quvchilar soni")


class CenterDistributionSerializer(Serializer):
    name = CharField(help_text="Tarif nomi")
    value = IntegerField(help_text="Tarif ulushi (foizda)")
    color = CharField(help_text="Grafik uchun HEX rang kodi")


class TopCentersSerializer(Serializer):
    id = CharField(help_text="Markaz ID raqami")
    name = CharField(help_text="Markaz nomi")
    students = IntegerField(help_text="O'quvchilar soni")
    percentage = IntegerField(help_text="Eng katta markazga nisbatan foiz ko'rsatkichi")


class ChartsSerializer(Serializer):
    revenue_12m = Revenue12MSerializer(many=True)
    student_growth = StudentGrowthSerializer(many=True)
    center_distribution = CenterDistributionSerializer(many=True)
    top_centers = TopCentersSerializer(many=True)


# ==========================================
# 3. RECENT ACTIVITIES VA ASOSIY SERIALIZER
# ==========================================
class RecentActivitySerializer(Serializer):
    id = CharField(help_text="Faoliyat IDsi")
    center_name = CharField(help_text="Markaz nomi")
    created_at = DateTimeField(help_text="Yaratilgan vaqti (ISO formatda)")
    status = CharField(help_text="Markaz holati (pending, active va h.k.)")


class DashboardDataSerializer(Serializer):
    kpi = KPISerializer()
    charts = ChartsSerializer()
    recent_activities = RecentActivitySerializer(many=True)


class SuperAdminDashboardSerializer(Serializer):
    status = CharField(default="success")
    data = DashboardDataSerializer()
