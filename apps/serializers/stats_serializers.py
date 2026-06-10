from rest_framework import serializers


# ================================
# 1. KPI QISMI UCHUN SERIALIZERLAR
# ================================
class BaseCenterStatsSerializer(serializers.Serializer):
    active = serializers.IntegerField(help_text="Faol markazlar soni")
    total = serializers.IntegerField(help_text="Jami markazlar soni")


class BaseStudentStatsSerializer(serializers.Serializer):
    new_this_month = serializers.IntegerField(
        help_text="Shu oyda qo'shilgan yangi o'quvchilar"
    )
    total = serializers.IntegerField(help_text="Jami o'quvchilar soni")


class BaseRevenueStatsSerializer(serializers.Serializer):
    total_this_month = serializers.IntegerField(help_text="Shu oydagi jami tushum")
    percentage_change = serializers.FloatField(
        help_text="O'tgan oyga nisbatan foizdagi farq"
    )
    is_up = serializers.BooleanField(help_text="Tushum o'sganmi yoki kamayganmi")


class BaseSubscriptionStatsSerializer(serializers.Serializer):
    trial = serializers.IntegerField(help_text="Trial tarifidagi markazlar soni")
    pro = serializers.IntegerField(help_text="Pro tarifidagi markazlar soni")
    enterprise = serializers.IntegerField(
        help_text="Enterprise tarifidagi markazlar soni"
    )
    total = serializers.IntegerField(help_text="Jami obunalar soni")


class BaseTicketStatsSerializer(serializers.Serializer):
    open = serializers.IntegerField(help_text="Ochiq ticketlar (ogohlantirishlar) soni")


class KPISerializer(serializers.Serializer):
    centers = BaseCenterStatsSerializer()
    students = BaseStudentStatsSerializer()
    revenue = BaseRevenueStatsSerializer()
    subscriptions = BaseSubscriptionStatsSerializer()
    tickets = BaseTicketStatsSerializer()


# ===================================
# 2. CHARTS (GRAFIKLAR) SERIALIZERLARI
# ===================================
class Revenue12MSerializer(serializers.Serializer):
    month = serializers.CharField(help_text="Oy nomi (Masalan: 'Yan')")
    amount = serializers.IntegerField(help_text="Oylik tushum miqdori")


class StudentGrowthSerializer(serializers.Serializer):
    month = serializers.CharField(help_text="Oy nomi")
    count = serializers.IntegerField(
        help_text="O'sha oydagi jami kumulyativ o'quvchilar soni"
    )


class CenterDistributionSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Tarif nomi")
    value = serializers.IntegerField(help_text="Tarif ulushi (foizda)")
    color = serializers.CharField(help_text="Grafik uchun HEX rang kodi")


class TopCentersSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Markaz ID raqami")
    name = serializers.CharField(help_text="Markaz nomi")
    students = serializers.IntegerField(help_text="O'quvchilar soni")
    percentage = serializers.IntegerField(
        help_text="Eng katta markazga nisbatan foiz ko'rsatkichi"
    )


class ChartsSerializer(serializers.Serializer):
    revenue_12m = Revenue12MSerializer(many=True)
    student_growth = StudentGrowthSerializer(many=True)
    center_distribution = CenterDistributionSerializer(many=True)
    top_centers = TopCentersSerializer(many=True)


# ==========================================
# 3. RECENT ACTIVITIES VA ASOSIY SERIALIZER
# ==========================================
class RecentActivitySerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Faoliyat IDsi")
    center_name = serializers.CharField(help_text="Markaz nomi")
    created_at = serializers.DateTimeField(help_text="Yaratilgan vaqti (ISO formatda)")
    status = serializers.CharField(help_text="Markaz holati (pending, active va h.k.)")


class DashboardDataSerializer(serializers.Serializer):
    kpi = KPISerializer()
    charts = ChartsSerializer()
    recent_activities = RecentActivitySerializer(many=True)


class SuperAdminDashboardSerializer(serializers.Serializer):
    status = serializers.CharField(default="success")
    data = DashboardDataSerializer()
