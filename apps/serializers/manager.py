from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DateField,
    DecimalField,
    EmailField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    TimeField,
    URLField,
    UUIDField,
)

from apps.models import User, Teacher, Student, Group, Room, Course, Payment
from apps.utils.phone import normalize_phone


class UserSummarySerializer(ModelSerializer):
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


# ─── STUDENT SERIALIZERS ───
class ManagerStudentListSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Student
        fields = ["id", "user", "status", "enrolled_at", "created_at"]


class ManagerStudentDetailSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    parent_name = SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
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


class ManagerStudentCreateSerializer(Serializer):
    phone = CharField(max_length=50, required=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    email = EmailField(required=False, allow_null=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=False)
    date_of_birth = DateField(required=False, allow_null=True)
    notes = CharField(required=False, allow_blank=True)
    status = ChoiceField(choices=Student.Status.choices, default=Student.Status.ACTIVE)
    parent = UUIDField(required=False, allow_null=True)

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        qs = User.objects.filter(phone=normalized)
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("Bu telefon raqam allaqachon mavjud.")
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        center = self.context.get("center")
        password = validated_data.pop("password", "123456")
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
            center=center,
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


# ─── TEACHER SERIALIZERS ───
class ManagerTeacherListSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "user", "specialization", "experience", "salary", "created_at"]


class ManagerTeacherDetailSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "user",
            "specialization",
            "experience",
            "salary",
            "bio",
            "date_of_birth",
            "created_at",
        ]


class ManagerTeacherCreateSerializer(Serializer):
    phone = CharField(max_length=50, required=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    email = EmailField(required=False, allow_null=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=False)
    specialization = CharField(max_length=255, required=False, allow_blank=True)
    experience = IntegerField(min_value=0, required=False, default=0)
    salary = DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    bio = CharField(required=False, allow_blank=True)
    date_of_birth = DateField(required=False, allow_null=True)

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        qs = User.objects.filter(phone=normalized)
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("Bu telefon raqam allaqachon mavjud.")
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        center = self.context.get("center")
        password = validated_data.pop("password", "123456")

        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email"),
            avatar=validated_data.get("avatar"),
            role=User.Role.TEACHER,
        )
        return Teacher.objects.create(
            user=user,
            center=center,
            specialization=validated_data.get("specialization", ""),
            experience=validated_data.get("experience", 0),
            salary=validated_data.get("salary"),
            bio=validated_data.get("bio", ""),
            date_of_birth=validated_data.get("date_of_birth"),
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user
        for field in ["phone", "first_name", "last_name", "email", "avatar"]:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        for field in ["specialization", "experience", "salary", "bio", "date_of_birth"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


# ─── GROUP & COURSE SERIALIZERS ───
class ManagerGroupCreateSerializer(Serializer):
    name = CharField(max_length=200)
    course = UUIDField()
    teacher = UUIDField()
    room = UUIDField(required=False, allow_null=True)
    status = ChoiceField(choices=Group.Status.choices, default=Group.Status.ACTIVE)
    start_date = DateField()
    end_date = DateField(required=False, allow_null=True)
    lesson_days = ListField(child=IntegerField(min_value=0, max_value=6))
    lesson_start_time = TimeField()
    lesson_end_time = TimeField()

    def validate(self, attrs):
        center = self.context.get("center")
        if attrs.get("course") and not Course.objects.filter(id=attrs["course"], center=center).exists():
            raise ValidationError({"course": "Kurs topilmadi yoki ushbu markazga tegishli emas."})
        if attrs.get("teacher") and not Teacher.objects.filter(id=attrs["teacher"], center=center).exists():
            raise ValidationError({"teacher": "O'qituvchi topilmadi yoki ushbu markazga tegishli emas."})
        if attrs.get("room") and not Room.objects.filter(id=attrs["room"], center=center).exists():
            raise ValidationError({"room": "Xona topilmadi yoki ushbu markazga tegishli emas."})
        if attrs.get("lesson_start_time") >= attrs.get("lesson_end_time"):
            raise ValidationError("Dars boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak.")
        return attrs

    def create(self, validated_data):
        center = self.context.get("center")
        return Group.objects.create(center=center, **validated_data)

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


# ─── PAYMENTS SERIALIZER ───
class ManagerPaymentSerializer(ModelSerializer):
    student = ManagerStudentListSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "student", "amount", "paid_at", "created_at"]
