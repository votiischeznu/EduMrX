# apps/serializers/profile.py

from rest_framework import serializers

from apps.models import User, Student, Teacher, Parent


class BaseUserProfileModelSerializer(serializers.ModelSerializer):
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


class ChildShortSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    center_name = serializers.CharField(source="center.name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "full_name", "phone", "center_name", "status"]


class ParentProfileSerializer(serializers.ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user", read_only=True)
    children = ChildShortSerializer(many=True, read_only=True)

    class Meta:
        model = Parent
        fields = ["id", "user_data", "occupation", "children"]
        read_only_fields = ["id", "children"]


class StudentProfileSerializer(serializers.ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user", read_only=True)
    center_name = serializers.CharField(source="center.name", read_only=True)
    parent_name = serializers.CharField(source="parent.user.full_name", read_only=True)

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


class TeacherProfileSerializer(serializers.ModelSerializer):
    user_data = BaseUserProfileModelSerializer(source="user", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "user_data", "specialization", "experience", "salary", "bio"]
        read_only_fields = ["id", "salary"]


class AdminProfileSerializer(serializers.ModelSerializer):
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


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Yangi parollar bir-biriga mos kelmadi."}
            )
        return attrs
