from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models import Parent, Student, Teacher, User


class UserUpdateMixin:
    def update(self, instance, validated_data):
        # 'user_data' bu yerda 'user' kaliti orqali keladi
        user_data = validated_data.pop("user", None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        return super().update(instance, validated_data)


class BaseUserProfileModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "email", "first_name", "last_name", "full_name", "role", "avatar", "gender"]
        read_only_fields = ["id", "phone", "role", "full_name"]


class ChildShortSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    center_name = CharField(source="center.name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "full_name", "phone", "center_name", "status"]


class ParentProfileSerializer(UserUpdateMixin, ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user")
    children = ChildShortSerializer(many=True, read_only=True)

    class Meta:
        model = Parent
        fields = ["id", "user_data", "occupation", "children"]
        read_only_fields = ["id", "children"]


class StudentProfileSerializer(UserUpdateMixin, ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user")
    center_name = CharField(source="center.name", read_only=True)
    parent_name = CharField(source="parent.user.full_name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "user_data", "center_name", "parent_name", "date_of_birth", "notes", "status", "enrolled_at"]
        read_only_fields = ["id", "center_name", "parent_name", "status", "enrolled_at"]


class TeacherProfileSerializer(UserUpdateMixin, ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user")

    class Meta:
        model = Teacher
        fields = ["id", "user_data", "specialization", "experience", "salary", "bio"]
        read_only_fields = ["id", "salary"]


class AdminProfileSerializer(ModelSerializer):
    center_ids = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "avatar",
            "gender",
            "center_ids",
        ]
        read_only_fields = ["id", "phone", "role", "full_name", "center_ids"]

    def get_center_ids(self, obj):
        staff = getattr(obj, "staff_profile", None)
        if staff and staff.center_id:
            return [staff.center_id]
        return []


class DirectorProfileSerializer(ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="*")
    center_ids = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "avatar",
            "gender",
            "center_ids",
        ]
        read_only_fields = ["id", "phone", "role", "full_name", "center_ids"]

    def get_center_ids(self, obj):
        return list(obj.directed_centers.values_list("id", flat=True))


class PasswordChangeSerializer(Serializer):
    old_password = CharField(required=True, write_only=True)
    new_password = CharField(required=True, write_only=True)
    confirm_password = CharField(required=True, write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise ValidationError({"old_password": "Eski parol noto'g'ri."})
        if attrs["new_password"] != attrs["confirm_password"]:
            raise ValidationError({"confirm_password": "Yangi parollar mos kelmadi."})
        validate_password(attrs["new_password"], user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        return user
