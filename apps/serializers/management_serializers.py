from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, EmailField, ImageField, SerializerMethodField, DateField
from rest_framework.serializers import ModelSerializer

from apps.models import Attendance, Parent, GroupStudent
from apps.models import Student, Teacher

User = get_user_model()


class ParentShortSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)

    class Meta:
        model = Parent
        fields = ["id", "full_name", "phone", "occupation"]


class StudentListSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    student_id = SerializerMethodField()

    class Meta:
        model = Student
        fields = ["id", "student_id", "full_name", "avatar", "phone", "email", "center_name", "status", "enrolled_at"]

    def get_student_id(self, obj) -> str:
        return f"STU-{obj.enrolled_at.year}-{str(obj.pk)[:4].upper()}"


class StudentDetailSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    student_id = SerializerMethodField()
    parent = ParentShortSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ["id", "student_id", "full_name", "avatar", "phone", "email", "center_name", "date_of_birth",
                  "address", "notes", "status", "enrolled_at", "parent"]

    def get_student_id(self, obj) -> str:
        return f"STU-{obj.enrolled_at.year}-{str(obj.pk)[:4].upper()}"


class TeacherListSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "full_name", "avatar", "phone", "email", "specialization", "experience"]


class TeacherDetailSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "full_name", "avatar", "phone", "email", "specialization", "experience", "salary", "bio"]


class AttendanceSerializer(ModelSerializer):
    student_name = CharField(source="student.user.full_name", read_only=True)
    student_phone = CharField(source="student.user.phone", read_only=True)
    lesson_date = DateField(source="lesson.date", read_only=True)
    group_name = CharField(source="lesson.group.name", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "lesson", "lesson_date", "group_name", "student", "student_name", "student_phone", "status",
                  "note", "marked_at"]
        read_only_fields = ["marked_at"]

    def validate(self, attrs):
        lesson = attrs.get('lesson')
        student = attrs.get('student')
        if lesson and student:
            if not GroupStudent.objects.filter(group=lesson.group, student=student, is_active=True).exists():
                raise ValidationError("Bu talaba ko'rsatilgan guruh faol talabalari ro'yxatida mavjud emas!")
        return attrs


class StudentCreateUpdateSerializer(ModelSerializer):
    full_name = CharField(write_only=True)
    phone = CharField(write_only=True)
    email = EmailField(write_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "full_name", "phone", "email",
            "center", "date_of_birth", "address",
            "notes", "status", "enrolled_at"
        ]

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        phone = validated_data.pop("phone")
        email = validated_data.pop("email")

        user = User.objects.create(
            full_name=full_name,
            phone=phone,
            email=email,
        )
        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        full_name = validated_data.pop("full_name", None)
        phone = validated_data.pop("phone", None)
        email = validated_data.pop("email", None)

        if full_name:
            instance.user.full_name = full_name
        if phone:
            instance.user.phone = phone
        if email:
            instance.user.email = email
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TeacherCreateUpdateSerializer(ModelSerializer):
    full_name = CharField(write_only=True)
    phone = CharField(write_only=True)
    email = EmailField(write_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id", "full_name", "phone", "email",
            "specialization", "experience", "salary", "bio"
        ]

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        phone = validated_data.pop("phone")
        email = validated_data.pop("email")

        user = User.objects.create(
            full_name=full_name,
            phone=phone,
            email=email,
        )
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher

    def update(self, instance, validated_data):
        full_name = validated_data.pop("full_name", None)
        phone = validated_data.pop("phone", None)
        email = validated_data.pop("email", None)

        if full_name:
            instance.user.full_name = full_name
        if phone:
            instance.user.phone = phone
        if email:
            instance.user.email = email
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
