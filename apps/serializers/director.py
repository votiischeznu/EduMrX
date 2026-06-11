from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DateField,
    EmailField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    URLField,
    UUIDField,
)

from apps.models.users import User
from apps.models.profiles import Student


class StudentUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "email",
        ]


class DirectorStudentListSerializer(ModelSerializer):
    user = StudentUserSerializer(read_only=True)
    center_name = CharField(source="center.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "center",
            "center_name",
            "status",
            "enrolled_at",
            "created_at",
        ]


class DirectorStudentDetailSerializer(ModelSerializer):
    user = StudentUserSerializer(read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    parent_name = SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "center",
            "center_name",
            "parent",
            "parent_name",
            "date_of_birth",
            "notes",
            "status",
            "enrolled_at",
            "created_at",
        ]

    def get_parent_name(self, obj):
        return obj.parent.full_name if obj.parent else None


class DirectorStudentCreateSerializer(Serializer):
    # User fields
    phone = CharField(max_length=50)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    email = EmailField(required=False, allow_null=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=False, default="EduMrX2025!")

    # Student fields
    center = UUIDField()
    date_of_birth = DateField(required=False, allow_null=True)
    notes = CharField(required=False, allow_blank=True)
    status = ChoiceField(choices=Student.Status.choices, default=Student.Status.ACTIVE)
    parent = UUIDField(required=False, allow_null=True)

    def validate_center(self, value):
        centers = self.context.get("centers")
        if not centers.filter(id=value).exists():
            raise PermissionDenied("Bu markaz sizga tegishli emas.")
        return value

    def validate_phone(self, value):
        qs = User.objects.filter(phone=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("Bu telefon raqam allaqachon mavjud.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        center_id = validated_data.pop("center")
        parent_id = validated_data.pop("parent", None)
        date_of_birth = validated_data.pop("date_of_birth", None)
        notes = validated_data.pop("notes", "")
        st_status = validated_data.pop("status", Student.Status.ACTIVE)

        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email"),
            avatar=validated_data.get("avatar"),
            role=User.Role.STUDENT,
        )
        return Student.objects.create(
            user=user,
            center_id=center_id,
            parent_id=parent_id,
            date_of_birth=date_of_birth,
            notes=notes,
            status=st_status,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user
        for field in ["phone", "first_name", "last_name", "email", "avatar"]:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        for field in ["date_of_birth", "notes", "status"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        if "parent" in validated_data:
            instance.parent_id = validated_data["parent"]
        instance.save()
        return instance
