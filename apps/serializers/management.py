from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, EmailField, ImageField, DateField
from rest_framework.fields import URLField, IntegerField
from rest_framework.serializers import ModelSerializer, Serializer

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
    avatar = URLField(source="user.avatar", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "full_name",
            "avatar",
            "phone",
            "email",
            "specialization",
            "experience",
            "salary",
            "bio",
        ]


class TeacherListSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    first_name = CharField(source="user.first_name", read_only=True)
    last_name = CharField(source="user.last_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = URLField(source="user.avatar", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "avatar",
            "phone",
            "email",
            "specialization",
            "experience",
            "salary",
            "bio",
            "date_of_birth",
            "centers",
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
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
            "password",
            "centers",
            "specialization",
            "experience",
            "salary",
            "bio",
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

        if first_name:
            instance.user.first_name = first_name
        if last_name:
            instance.user.last_name = last_name
        if phone:
            instance.user.phone = phone
        if email:
            instance.user.email = email
        if password:
            instance.user.set_password(password)
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
    avatar = URLField(source="user.avatar", read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    student_id = CharField(source="generated_student_id", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "full_name",
            "first_name",
            "last_name",
            "avatar",
            "phone",
            "email",
            "center_name",
            "status",
            "date_of_birth",
            "enrolled_at",
        ]


class StudentDetailSerializer(ModelSerializer):
    full_name = CharField(source="user.full_name", read_only=True)
    phone = CharField(source="user.phone", read_only=True)
    email = EmailField(source="user.email", read_only=True)
    avatar = ImageField(source="user.avatar", read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    parent = ParentShortSerializer(read_only=True)
    parent_phone = CharField(
        source="parent.user.phone", read_only=True, allow_null=True
    )
    student_id = CharField(source="generated_student_id", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "full_name",
            "avatar",
            "phone",
            "email",
            "center_name",
            "date_of_birth",
            "notes",
            "status",
            "enrolled_at",
            "parent",
            "parent_phone",
        ]

    def get_student_id(self, obj) -> str:
        return f"STU-{obj.enrolled_at.year}-{str(obj.pk)[:4].upper()}"


class StudentCreateUpdateSerializer(ModelSerializer):
    first_name = CharField(write_only=True)
    last_name = CharField(write_only=True)
    phone = CharField(write_only=True)
    email = EmailField(write_only=True, required=False, allow_null=True)
    password = CharField(write_only=True, required=False)

    parent_name = CharField(write_only=True, required=False, allow_blank=True)
    parent_phone = CharField(write_only=True, required=False, allow_blank=True)

    parent = ParentShortSerializer(read_only=True)
    parent_phone_display = CharField(source="parent.user.phone", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
            "password",
            "parent",
            "parent_phone_display",
            "parent_name",
            "parent_phone",
            "center",
            "date_of_birth",
            "notes",
            "status",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "phone": {"required": True},
            "email": {"required": False, "allow_null": True},
            "date_of_birth": {"required": False, "allow_null": True},
        }

    def validate_email(self, value):
        if value:
            if User.objects.filter(email=value).exists():
                raise ValidationError(
                    "Bu elektron pochta allaqachon ro'yxatdan o'tgan."
                )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")
        phone = validated_data.pop("phone")
        email = validated_data.pop("email", None)

        parent_name = validated_data.pop("parent_name", "").strip()
        parent_phone = validated_data.pop("parent_phone", "").strip()

        # 🔹 Student user create
        user = User.objects.create_user(
            phone=phone,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role=User.Role.STUDENT,
        )

        parent = None

        if parent_name:
            if parent_phone:
                parent = Parent.objects.filter(user__phone=parent_phone).first()

            if not parent:
                parent_user = User.objects.create_user(
                    phone=parent_phone if parent_phone else None,
                    first_name=parent_name,
                    password=None,
                    role=User.Role.PARENT,
                )
                parent = Parent.objects.create(user=parent_user)

        return Student.objects.create(user=user, parent=parent, **validated_data)

    def update(self, instance, validated_data):
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        phone = validated_data.pop("phone", None)
        email = validated_data.pop("email", None)
        password = validated_data.pop("password", None)

        parent_name = validated_data.pop("parent_name", None)
        parent_phone = validated_data.pop("parent_phone", None)

        if first_name:
            instance.user.first_name = first_name
        if last_name:
            instance.user.last_name = last_name
        if phone:
            instance.user.phone = phone
        if email:
            instance.user.email = email
        if password:
            instance.user.set_password(password)
        instance.user.save()

        if parent_name is not None:
            parent_name = parent_name.strip()

            if parent_name:
                parent = None

                if parent_phone:
                    parent = Parent.objects.filter(user__phone=parent_phone).first()

                if not parent:
                    parent_user = User.objects.create_user(
                        phone=parent_phone if parent_phone else None,
                        first_name=parent_name,
                        password=None,
                        role=User.Role.PARENT,
                    )
                    parent = Parent.objects.create(user=parent_user)

                instance.parent = parent
            else:
                instance.parent = None

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
        fields = [
            "id",
            "lesson",
            "lesson_date",
            "group_name",
            "student",
            "student_name",
            "student_phone",
            "status",
            "note",
            "marked_at",
        ]
        read_only_fields = ["marked_at"]

    def validate(self, attrs):
        lesson = attrs.get("lesson")
        student = attrs.get("student")
        if lesson and student:
            if not GroupStudent.objects.filter(
                group=lesson.group, student=student, is_active=True
            ).exists():
                raise ValidationError(
                    "Bu talaba ko'rsatilgan guruh faol talabalari ro'yxatida mavjud emas!"
                )
        return attrs


class StudentStatsResponseSerializer(Serializer):
    active = IntegerField(help_text="Faol talabalar soni")
    new_this_month = IntegerField(help_text="Shu oyda qo'shilgan yangi talabalar soni")
    minus_this_month = IntegerField(
        help_text="Shu oyda chiqib ketgan/muzlatilgan talabalar soni"
    )
