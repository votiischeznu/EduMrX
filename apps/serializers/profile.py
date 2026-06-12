from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import Serializer, ModelSerializer
from apps.models import User, Student, Teacher, Parent


class BaseUserProfileModelSerializer(ModelSerializer):
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
        ]
        read_only_fields = ["id", "phone", "role", "full_name"]


class ChildShortSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    center_name = CharField(source="center.name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "full_name", "phone", "center_name", "status"]


class ParentProfileSerializer(ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user", read_only=True)
    children = ChildShortSerializer(many=True, read_only=True)

    class Meta:
        model = Parent
        fields = ["id", "user_data", "occupation", "children"]
        read_only_fields = ["id", "children"]


class StudentProfileSerializer(ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user", read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    parent_name = CharField(source="parent.user.full_name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "user_data",
            "center_name",
            "parent_name",
            "date_of_birth",
            "address",
            "status",
            "enrolled_at",
        ]
        read_only_fields = ["id", "center_name", "parent_name", "status", "enrolled_at"]


class TeacherProfileSerializer(ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "user_data", "specialization", "experience", "salary", "bio"]
        read_only_fields = ["id", "salary"]


class AdminProfileSerializer(ModelSerializer):
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
        ]
        read_only_fields = ["id", "phone", "role"]


class PasswordChangeSerializer(Serializer):
    old_password = CharField(required=True, write_only=True)
    new_password = CharField(required=True, write_only=True)
    confirm_password = CharField(required=True, write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise ValidationError({"old_password": "Eski parol noto‘g‘ri."})

        if attrs["new_password"] != attrs["confirm_password"]:
            raise ValidationError({"confirm_password": "Yangi parollar mos kelmadi."})
        validate_password(attrs["new_password"], user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        if user.must_change_password:
            user.must_change_password = False
        user.save()
        return user
