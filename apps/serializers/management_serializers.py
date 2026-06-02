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


class TeacherDetailSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "full_name", "avatar", "phone", "email", "specialization", "experience", "salary", "bio"]


class TeacherListSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    first_name = CharField(source="user.first_name", read_only=True)
    last_name = CharField(source="user.last_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id", "full_name", "first_name", "last_name",
            "avatar", "phone", "email",
            "specialization", "experience", "salary", "bio",
            "date_of_birth", "centers",
        ]


class TeacherCreateUpdateSerializer(ModelSerializer):
    first_name = CharField(write_only=True)
    last_name = CharField(write_only=True)
    phone = CharField(write_only=True)
    email = EmailField(write_only=True, required=False, allow_null=True)
    password = CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Teacher
        fields = [
            "id", "first_name", "last_name", "phone", "email", "password",
            "centers", "specialization", "experience", "salary", "bio",
            "date_of_birth",  # ✅
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "phone": {"required": True},
            "email": {"required": False, "allow_null": True},
            "date_of_birth": {"required": False, "allow_null": True},  # ✅
        }

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        phone = validated_data.pop("phone")
        email = validated_data.pop("email", None)

        user = User.objects.create_user(
            phone=phone,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role=User.Role.TEACHER,
        )
        return Teacher.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        phone = validated_data.pop("phone", None)
        email = validated_data.pop("email", None)
        password = validated_data.pop("password", None)

        if first_name: instance.user.first_name = first_name
        if last_name: instance.user.last_name = last_name
        if phone: instance.user.phone = phone
        if email: instance.user.email = email
        if password: instance.user.set_password(password)
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StudentListSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    first_name = CharField(source="user.first_name", read_only=True)
    last_name = CharField(source="user.last_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    student_id = CharField(source="generated_student_id", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "student_id", "full_name", "first_name", "last_name", "avatar", "phone", "email",
                  "center_name", "status", "address", "date_of_birth", "latitude", "longitude", "enrolled_at"]

class StudentDetailSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    parent = ParentShortSerializer(read_only=True)
    student_id = CharField(source="generated_student_id", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "student_id", "full_name", "avatar", "phone", "email", "center_name", "date_of_birth",
                  "address", "notes", "status", "enrolled_at", "parent"]

    def get_student_id(self, obj) -> str:
        return f"STU-{obj.enrolled_at.year}-{str(obj.pk)[:4].upper()}"


class StudentCreateUpdateSerializer(ModelSerializer):
    first_name = CharField(write_only=True)
    last_name = CharField(write_only=True)
    phone = CharField(write_only=True)
    email = EmailField(write_only=True, required=False, allow_null=True)
    password = CharField(write_only=True, required=False)

    class Meta:
        model = Student
        fields = [
            "id", "first_name", "last_name", "phone", "email", "password",
            "center", "date_of_birth", "address" , "latitude", "longitude", "notes", "status"
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "phone": {"required": True},
            "email": {"required": False, "allow_null": True},
            "date_of_birth": {"required": False, "allow_null": True},
            "address": {"required": False, "allow_blank": True},
            "latitude": {"required": False, "allow_null": True},
            "longitude": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        return attrs

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        phone = validated_data.pop("phone")
        email = validated_data.pop("email", None)

        user = User.objects.create_user(
            phone=phone,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role=User.Role.STUDENT,
        )
        return Student.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        phone = validated_data.pop("phone", None)
        email = validated_data.pop("email", None)
        password = validated_data.pop("password", None)

        if first_name: instance.user.first_name = first_name
        if last_name: instance.user.last_name = last_name
        if phone: instance.user.phone = phone
        if email: instance.user.email = email
        if password: instance.user.set_password(password)
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


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
