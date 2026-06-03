import os
import re

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ImageField, SerializerMethodField, BooleanField
from rest_framework.serializers import ModelSerializer

from apps.models import Center

User = get_user_model()


class CenterListSerializer(ModelSerializer):
    director_name = CharField(source="director.full_name", read_only=True)
    students_count = SerializerMethodField()

    class Meta:
        model = Center
        fields = ["id", "name", "slug", "logo", "phone", "email", "address",
                  "status", "director_name", "students_count", "subscription_expires"]

    def get_students_count(self, obj) -> int:
        return obj.students.count()


class CenterDetailSerializer(ModelSerializer):
    director_name = CharField(source="director.full_name", read_only=True)
    director_phone = CharField(source="director.phone", read_only=True)
    students_count = SerializerMethodField()
    teachers_count = SerializerMethodField()
    is_subscription_active = BooleanField(read_only=True)

    class Meta:
        model = Center
        fields = ["id", "name", "slug", "logo", "phone", "email", "address",
                  "status", "director", "director_name", "director_phone",
                  "subscription_expires", "is_subscription_active",
                  "students_count", "teachers_count", "created_at"]

    def get_students_count(self, obj) -> int:
        return obj.students.count()

    def get_teachers_count(self, obj) -> int:
        return obj.teachers.count()


class CenterCreateUpdateSerializer(ModelSerializer):
    logo = ImageField(required=False, allow_null=True)

    def validate_logo(self, value):
        if not value:
            return None

        if hasattr(value, 'name'):
            name, ext = os.path.splitext(value.name)
            clean_name = slugify(name)
            value.name = f"{clean_name}{ext}"

        return value

    class Meta:
        model = Center
        fields = ["id", "name", "slug", "logo", "phone", "email", "address" , "latitude", "longitude", "director", "status", "subscription_expires"]

    def validate_slug(self, value):
        SLUG_REGEX = r'^[a-z0-9-_]+$'
        if not re.match(SLUG_REGEX, value):
            raise ValidationError(
                "Slug formati noto'g'ri. Faqat kichik ingliz harflari, "
                "raqamlar va chiziqchadan (- yoki _) foydalanish mumkin (Probellar mumkin emas)."
            )
        return value


class DirectorCreateUpdateSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "phone", "email", "password"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "phone": {"required": True},
            "email": {"required": False, "allow_null": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(
            role=User.Role.DIRECTOR,
            password=password,
            **validated_data
        )

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
        fields = ["id", "full_name", "phone", "email", "avatar", "created_at"]
