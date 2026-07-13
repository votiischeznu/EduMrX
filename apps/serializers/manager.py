from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
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

from apps.models import Course, Group, Parent, Payment, Room, Student, Teacher, User
from apps.utils.phone import normalize_phone


def _generate_temp_password() -> str:
    """Har bir foydalanuvchi uchun bir xil emas, tasodifiy vaqtinchalik parol."""
    return get_random_string(10)


class UserSummarySerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name", "full_name", "avatar", "email"]


# ==========================================
# STUDENTS
# ==========================================


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
    email = EmailField(required=False, allow_null=True, allow_blank=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=False, allow_blank=True)
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

    def validate_email(self, value):
        # Frontend bo'sh string yuborishi mumkin — buni "email berilmadi" deb qaraymiz.
        if not value:
            return None
        value = value.strip().lower()
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return value

    def validate_parent(self, value):
        if value is None:
            return value
        if not Parent.objects.filter(id=value).exists():
            raise ValidationError("Ota-ona topilmadi.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        center = self.context.get("center")
        branch = self.context.get("branch")

        raw_password = validated_data.pop("password", "") or None
        password = raw_password or _generate_temp_password()

        parent_id = validated_data.pop("parent", None)
        date_of_birth = validated_data.pop("date_of_birth", None)
        notes = validated_data.pop("notes", "")
        st_status = validated_data.pop("status", Student.Status.ACTIVE)

        # FIX: rol har doim serverda qattiq belgilanadi (STUDENT) — foydalanuvchi
        # yuborgan ma'lumotdan olinmaydi. Manager hech qachon boshqa rol
        # (director/super_admin) bilan foydalanuvchi yarata olmaydi.
        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email"),
            avatar=validated_data.get("avatar"),
            role=User.Role.STUDENT,
        )
        if raw_password is None:
            # Manager parol bermagan — birinchi kirishda o'zgartirishga majburlaymiz.
            user.must_change_password = True
            user.save(update_fields=["must_change_password"])

        return Student.objects.create(
            user=user,
            center=center,
            branch=branch,
            parent_id=parent_id,
            date_of_birth=date_of_birth,
            notes=notes,
            status=st_status,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user
        validated_data.pop("password", None)  # PATCH orqali parol o'zgartirilmaydi
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


# ==========================================
# TEACHERS
# ==========================================


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
    email = EmailField(required=False, allow_null=True, allow_blank=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=False, allow_blank=True)
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

    def validate_email(self, value):
        if not value:
            return None
        value = value.strip().lower()
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        center = self.context.get("center")
        branch = self.context.get("branch")

        raw_password = validated_data.pop("password", "") or None
        password = raw_password or _generate_temp_password()

        # FIX: rol qattiq TEACHER — manager bu orqali director/admin/super_admin
        # rolidagi foydalanuvchi yarata olmaydi.
        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email"),
            avatar=validated_data.get("avatar"),
            role=User.Role.TEACHER,
        )
        if raw_password is None:
            user.must_change_password = True
            user.save(update_fields=["must_change_password"])

        return Teacher.objects.create(
            user=user,
            centers=center,
            branch=branch,
            specialization=validated_data.get("specialization", ""),
            experience=validated_data.get("experience", 0),
            salary=validated_data.get("salary"),
            bio=validated_data.get("bio", ""),
            date_of_birth=validated_data.get("date_of_birth"),
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user
        validated_data.pop("password", None)
        for field in ["phone", "first_name", "last_name", "email", "avatar"]:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        for field in ["specialization", "experience", "salary", "bio", "date_of_birth"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


# ==========================================
# GROUPS
# ==========================================


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
        branch = self.context.get("branch")

        if attrs.get("course") and not Course.objects.filter(id=attrs["course"], center=center).exists():
            raise ValidationError({"course": "Kurs topilmadi yoki ushbu markazga tegishli emas."})

        if attrs.get("teacher"):
            teacher_exists = Teacher.objects.filter(id=attrs["teacher"], centers=center, branch=branch).exists()
            if not teacher_exists:
                raise ValidationError({"teacher": "O'qituvchi topilmadi yoki ushbu filialga tegishli emas."})

        if attrs.get("room"):
            room_exists = Room.objects.filter(id=attrs["room"], center=center, branch=branch).exists()
            if not room_exists:
                raise ValidationError({"room": "Xona topilmadi yoki ushbu filialga tegishli emas."})

        # FIX: avval "attrs.get('lesson_start_time') >= attrs.get('lesson_end_time')"
        # shartsiz solishtirilardi. Partial PATCH'da bu ikki maydon yuborilmasa
        # ikkalasi ham None bo'lib, "'>=' not supported between instances of
        # 'NoneType' and 'NoneType'" TypeError (500 Internal Server Error) berardi.
        # Endi faqat ikkalasi ham mavjud bo'lgandagina solishtiramiz.
        lesson_start_time = attrs.get("lesson_start_time")
        lesson_end_time = attrs.get("lesson_end_time")
        if lesson_start_time and lesson_end_time and lesson_start_time >= lesson_end_time:
            raise ValidationError("Dars boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak.")

        # FIX: xuddi shu sabab bilan end_date/start_date solishtiruvi ham
        # partial PATCH'da start_date yuborilmasa xatolik berishi mumkin edi.
        end_date = attrs.get("end_date")
        start_date = attrs.get("start_date")
        if end_date and start_date and end_date <= start_date:
            raise ValidationError({"end_date": "Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        center = self.context.get("center")
        branch = self.context.get("branch")

        # Django FK maydoniga UUID emas, model instance yoki `<field>_id` kutadi.
        course_id = validated_data.pop("course")
        teacher_id = validated_data.pop("teacher")
        room_id = validated_data.pop("room", None)

        return Group.objects.create(
            center=center,
            branch=branch,
            course_id=course_id,
            teacher_id=teacher_id,
            room_id=room_id,
            **validated_data,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        if "course" in validated_data:
            instance.course_id = validated_data.pop("course")
        if "teacher" in validated_data:
            instance.teacher_id = validated_data.pop("teacher")
        if "room" in validated_data:
            instance.room_id = validated_data.pop("room")

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance


# ==========================================
# PAYMENTS
# ==========================================


class ManagerPaymentSerializer(ModelSerializer):
    """
    O'quvchi to'lovlarini ko'rsatish uchun.

    Eslatma: to'lovni KIM to'lagani (o'quvchining o'zi yoki ota-onasi)
    modelda alohida saqlanmaydi — Payment har doim `student`ga bog'lanadi.
    Shu sababli ota-ona to'lov qilsa ham, u aynan shu student'ning to'lovi
    sifatida to'g'ri qayd etiladi va manager ro'yxatida ko'rinadi.
    """
    student = ManagerStudentListSerializer(read_only=True)
    class Meta:
        model = Payment
        fields = [
            "id",
            "student",
            "group",
            "amount",
            "discount",
            "final_amount",
            "method",
            "status",
            "period_month",
            "period_year",
            "due_date",
            "paid_at",
            "receipt_number",
            "comment",
            "created_at",
        ]


class ManagerPaymentCreateSerializer(Serializer):
    """
    Manager tomonidan qo'lda to'lov kiritish uchun (masalan naqd to'lov
    reception oynasida qabul qilinganda). Yaratilgan to'lov darhol
    status=PAID va paid_at=now bilan yoziladi — "naqd to'ladi, tizimga
    kiritildi" ssenariysi uchun.
    """

    student = UUIDField()
    group = UUIDField(required=False, allow_null=True)
    amount = DecimalField(max_digits=12, decimal_places=2)
    discount = DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    method = ChoiceField(choices=Payment.Method.choices, default=Payment.Method.CASH)
    period_month = IntegerField(min_value=1, max_value=12)
    period_year = IntegerField()
    comment = CharField(required=False, allow_blank=True)

    def validate_student(self, value):
        center = self.context.get("center")
        branch = self.context.get("branch")
        if not Student.objects.filter(
            id=value, center=center, branch=branch, user__is_deleted=False
        ).exists():
            raise ValidationError("O'quvchi topilmadi yoki sizning filialingizga tegishli emas.")
        return value

    def validate_group(self, value):
        if value is None:
            return value
        center = self.context.get("center")
        branch = self.context.get("branch")
        if not Group.objects.filter(id=value, center=center, branch=branch).exists():
            raise ValidationError("Guruh topilmadi yoki sizning filialingizga tegishli emas.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        branch = self.context.get("branch")

        student_id = validated_data.pop("student")
        group_id = validated_data.pop("group", None)

        return Payment.objects.create(
            student_id=student_id,
            group_id=group_id,
            branch=branch,
            due_date=timezone.now().date(),
            status=Payment.Status.PAID,
            paid_at=timezone.now(),
            **validated_data,
        )