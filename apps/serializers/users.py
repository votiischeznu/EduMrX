from rest_framework import serializers
from apps.models import Student


class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)
    student_id = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "full_name",
            "avatar",
            "phone",
            "email",
            "status",
            "enrolled_at",
        ]

    def get_student_id(self, obj) -> str:
        return f"STU-{obj.enrolled_at.year}-{str(obj.pk)[:3].upper()}"


class ParentShortSerializer(serializers.Serializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    occupation = serializers.CharField(read_only=True)


class StudentDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)
    student_id = serializers.SerializerMethodField()
    parent = ParentShortSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "full_name",
            "avatar",
            "phone",
            "email",
            "date_of_birth",
            "address",
            "notes",
            "status",
            "enrolled_at",
            "parent",
            "created_at",
            "updated_at",
        ]

    def get_student_id(self, obj) -> str:
        return f"STU-{obj.enrolled_at.year}-{str(obj.pk)[:3].upper()}"
