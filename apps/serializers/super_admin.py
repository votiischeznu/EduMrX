import re

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.fields import JSONField, CharField, IntegerField, BooleanField
from rest_framework.serializers import Serializer, ModelSerializer

from apps.models import Center
from apps.utils.phone import normalize_phone

User = get_user_model()


class SuperAdminMenuStatsSerializer(Serializer):
    dashboards = JSONField()
    students = JSONField()
    directors = JSONField()
    centers = JSONField()
    payments = JSONField()


class DirectorCreateUpdateSerializer(ModelSerializer):
    password = CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
            "password",
            "is_active",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "phone": {"required": True},
            "email": {"required": False, "allow_null": True},
            "is_active": {"read_only": True},
        }

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        user_id = self.instance.id if self.instance else None
        if (
            User.objects.filter(phone=normalized, is_deleted=False)
            .exclude(id=user_id)
            .exists()
        ):
            raise ValidationError(
                "Bu telefon raqam allaqachon boshqa direktor tomonidan band qilingan."
            )
        return normalized

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise ValidationError(
                {"password": "Yangi direktor uchun parol kiritish majburiy."}
            )

        user = User.objects.create_user(
            role=User.Role.DIRECTOR, password=password, **validated_data
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class DirectorListSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
            "is_active",
            "created_at",
        ]


class CenterStudentCountSerializer(ModelSerializer):
    director_name = CharField(source="director.full_name", read_only=True)
    total_students_count = IntegerField(read_only=True)
    active_students_count = IntegerField(read_only=True)

    class Meta:
        model = Center
        fields = [
            "id",
            "name",
            "slug",
            "phone",
            "director_name",
            "total_students_count",
            "active_students_count",
        ]


class CenterListSerializer(ModelSerializer):
    director_name = CharField(source="director.full_name", read_only=True)
    students_count = IntegerField(read_only=True)

    class Meta:
        model = Center
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "phone",
            "email",
            "address",
            "longitude",
            "latitude",
            "status",
            "plan",
            "director",
            "director_name",
            "students_count",
            "subscription_expires",
        ]


class CenterDetailSerializer(ModelSerializer):
    director_name = CharField(source="director.full_name", read_only=True)
    director_phone = CharField(source="director.phone", read_only=True)
    students_count = IntegerField(read_only=True)
    teachers_count = IntegerField(read_only=True)
    is_subscription_active = BooleanField(read_only=True)

    class Meta:
        model = Center
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "phone",
            "email",
            "address",
            "status",
            "plan",
            "director",
            "director_name",
            "director_phone",
            "longitude",
            "latitude",
            "subscription_expires",
            "is_subscription_active",
            "students_count",
            "teachers_count",
            "created_at",
        ]

    def validate_slug(self, value):
        SLUG_REGEX = r"^[a-z0-9-_]+$"
        if not re.match(SLUG_REGEX, value):
            raise ValidationError(
                "Slug formati noto'g'ri. Faqat kichik harflar va chiziqchalar mumkin."
            )
        return value


class PlanStatsSerializer(Serializer):
    trial = IntegerField(help_text="Trial tarifidagi markazlar soni")
    pro = IntegerField(help_text="Pro tarifidagi markazlar soni")
    max = IntegerField(help_text="Max tarifidagi markazlar soni")
    enterprise = IntegerField(help_text="Enterprise tarifidagi markazlar soni")
