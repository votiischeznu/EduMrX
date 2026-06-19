from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

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

from apps.models import User, Teacher, Student, Group, GroupStudent, Room, Course, Lesson, Attendance
from apps.serializers.utils import normalize_phone


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


class DirectorStudentListSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    center_name = CharField(source="center.name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "user", "center", "center_name", "status", "enrolled_at", "created_at"]


class DirectorStudentDetailSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)
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
            "date_of_birth",
            "notes",
            "status",
            "enrolled_at",
            "created_at",
        ]

    def get_parent_name(self, obj):
        return obj.parent.full_name if obj.parent else None


class DirectorStudentCreateSerializer(Serializer):
    phone = CharField(max_length=50, required=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    email = EmailField(required=False, allow_null=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=True)
    center = UUIDField()
    date_of_birth = DateField(required=False, allow_null=True)
    notes = CharField(required=False, allow_blank=True)
    status = ChoiceField(choices=Student.Status.choices, default=Student.Status.ACTIVE)
    parent = UUIDField(required=False, allow_null=True)

    def validate_center(self, value):
        centers = self.context.get("centers")
        if centers is None:
            raise PermissionDenied("Markaz konteksti topilmadi.")
        if not centers.filter(id=value).exists():
            raise PermissionDenied("Bu markaz sizga tegishli emas.")
        return value

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        qs = User.objects.filter(phone=normalized)
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


class DirectorTeacherListSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id",
            "user",
            "specialization",
            "experience",
            "salary",
            "created_at",
        ]


class DirectorTeacherDetailSerializer(ModelSerializer):
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


class DirectorTeacherCreateSerializer(Serializer):
    phone = CharField(max_length=50, required=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    email = EmailField(required=False, allow_null=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=True)

    specialization = CharField(max_length=255, required=False, allow_blank=True)
    experience = IntegerField(min_value=0, required=False, default=0)
    salary = DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    bio = CharField(required=False, allow_blank=True)
    date_of_birth = DateField(required=False, allow_null=True)

    def validate_phone(self, value):
        qs = User.objects.filter(phone=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("Bu telefon raqam allaqachon mavjud.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        center = self.context.get("center")
        if not center:
            raise ValidationError("Faol markaz topilmadi.")
        password = validated_data.pop("password")

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
            center=center,  # ForeignKey: 'centers' → 'center' deb model bilan moslashtiring
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


class DirectorRoomSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "capacity"]


class DirectorCourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "duration_months",
            "price",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DirectorGroupStudentSerializer(ModelSerializer):
    student_name = SerializerMethodField()
    phone = SerializerMethodField()

    class Meta:
        model = GroupStudent
        fields = ["id", "student", "student_name", "phone", "joined_at", "is_active"]
        read_only_fields = ["id", "joined_at"]

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() if obj.student and obj.student.user else None

    def get_phone(self, obj):
        return obj.student.user.phone if obj.student and obj.student.user else None


class DirectorGroupListSerializer(ModelSerializer):
    course_name = CharField(source="course.name", read_only=True)
    teacher_name = SerializerMethodField()
    room_name = CharField(source="room.name", read_only=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "course",
            "course_name",
            "teacher",
            "teacher_name",
            "room",
            "room_name",
            "status",
            "student_count",
            "start_date",
            "end_date",
            "lesson_days",
            "lesson_start_time",
            "lesson_end_time",
        ]

    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name()
        return None


class DirectorGroupDetailSerializer(DirectorGroupListSerializer):
    enrollments = DirectorGroupStudentSerializer(many=True, read_only=True)

    class Meta(DirectorGroupListSerializer.Meta):
        fields = DirectorGroupListSerializer.Meta.fields + ["enrollments"]


class DirectorGroupCreateSerializer(Serializer):
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

    def validate_course(self, value):
        center = self.context.get("center")
        if not center:
            raise ValidationError("Markaz konteksti topilmadi.")
        if not Course.objects.filter(id=value, center=center).exists():
            raise PermissionDenied("Bu kurs sizning markazingizga tegishli emas.")
        return value

    def validate_teacher(self, value):
        center = self.context.get("center")
        if not center:
            raise ValidationError("Markaz konteksti topilmadi.")
        # Teacher modelidagi maydon nomini o'zingiznikiga moslashtiring (center yoki centers)
        if not Teacher.objects.filter(id=value, center=center).exists():
            raise PermissionDenied("Bu o'qituvchi sizning markazingizga tegishli emas.")
        return value

    def validate_lesson_days(self, value):
        if len(value) != len(set(value)):
            raise ValidationError("Takroriy kunlar kiritilgan.")
        return value

    def validate(self, attrs):
        if attrs.get("lesson_start_time") and attrs.get("lesson_end_time"):
            if attrs["lesson_start_time"] >= attrs["lesson_end_time"]:
                raise ValidationError("Dars boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        center = self.context.get("center")
        if not center:
            raise ValidationError("Faol markaz topilmadi.")
        return Group.objects.create(center=center, **validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class DirectorGroupEnrollSerializer(Serializer):
    student_id = UUIDField()
    action = ChoiceField(choices=["add", "remove"])

    def validate_student_id(self, value):
        center = self.context.get("center")
        if not center:
            raise ValidationError("Markaz konteksti topilmadi.")
        if not Student.objects.filter(id=value, center=center, user__is_deleted=False).exists():
            raise PermissionDenied("Bu student sizning markazingizga tegishli emas.")
        return value

    def save(self):
        group = self.context["group"]
        student_id = self.validated_data["student_id"]
        action = self.validated_data["action"]

        if action == "add":
            if group.is_full:
                raise ValidationError("Guruh to'lgan, joy yo'q.")
            GroupStudent.objects.get_or_create(group=group, student_id=student_id)
        else:
            GroupStudent.objects.filter(group=group, student_id=student_id).delete()

        group.refresh_from_db()
        return group


class DirectorLessonListSerializer(ModelSerializer):
    group_name = CharField(source="group.name", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "group",
            "group_name",
            "date",
            "start_time",
            "end_time",
            "topic",
            "notes",
        ]
        read_only_fields = ["id"]


class DirectorLessonCreateSerializer(Serializer):
    group = UUIDField()
    date = DateField()
    start_time = TimeField()
    end_time = TimeField()
    topic = CharField(max_length=300, required=False, allow_blank=True)
    notes = CharField(required=False, allow_blank=True)

    def validate_group(self, value):
        center = self.context.get("center")
        if not center:
            raise ValidationError("Markaz konteksti topilmadi.")
        if not Group.objects.filter(id=value, center=center).exists():
            raise PermissionDenied("Bu guruh sizning markazingizga tegishli emas.")
        return value

    def validate(self, attrs):
        if attrs.get("start_time") and attrs.get("end_time"):
            if attrs["start_time"] >= attrs["end_time"]:
                raise ValidationError("Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak.")
        return attrs

    def create(self, validated_data):
        return Lesson.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class DirectorAttendanceSerializer(ModelSerializer):
    student_name = SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ["id", "student", "student_name", "status", "note", "marked_at"]
        read_only_fields = ["id", "marked_at"]

    def get_student_name(self, obj):
        if obj.student and obj.student.user:
            return obj.student.user.get_full_name()
        return None


class DirectorAttendanceBulkSerializer(Serializer):
    class RecordSerializer(Serializer):
        student = UUIDField()
        status = ChoiceField(choices=Attendance.Status.choices, default=Attendance.Status.PRESENT)
        note = CharField(required=False, allow_blank=True, default="")

    records = RecordSerializer(many=True)

    def validate_records(self, value):
        if not value:
            raise ValidationError("Kamida bitta yozuv bo'lishi kerak.")
        return value

    @transaction.atomic
    def save(self):
        lesson = self.context["lesson"]
        records = self.validated_data["records"]

        results = []
        for rec in records:
            obj, _ = Attendance.objects.update_or_create(
                lesson=lesson,
                student_id=rec["student"],
                defaults={"status": rec["status"], "note": rec.get("note", "")},
            )
            results.append(obj)
        return results
