from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DateField,
    DecimalField,
    EmailField,
    IntegerField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    TimeField,
    URLField,
    UUIDField,
)
from apps.service import get_director_centers
from apps.models import Attendance, CenterStaff, Course, Group, GroupStudent, Lesson, Room, Student, Teacher, User, Branch
from apps.utils.phone import normalize_phone


class UserSummarySerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name", "full_name", "avatar", "email"]


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
    branch = UUIDField(required=False, allow_null=True)
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

    def validate_branch(self, value):
        if value is None:
            return value
        centers = self.context.get("centers")
        from apps.models import Branch

        if not Branch.objects.filter(id=value, center__in=centers).exists():
            raise PermissionDenied("Bu filial sizga tegishli emas.")
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
        branch_id = validated_data.pop("branch", None)
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
            branch_id=branch_id,
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
        if "branch" in validated_data:
            instance.branch_id = validated_data["branch"]


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
        fields = ["id", "user", "specialization", "experience", "salary", "bio", "date_of_birth", "created_at"]


class DirectorTeacherCreateSerializer(Serializer):
    phone = CharField(max_length=50, required=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    email = EmailField(required=False, allow_null=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=True)
    center = UUIDField()
    branch = UUIDField(required=False, allow_null=True)
    specialization = CharField(max_length=255, required=False, allow_blank=True)
    experience = IntegerField(min_value=0, required=False, default=0)
    salary = DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    bio = CharField(required=False, allow_blank=True)
    date_of_birth = DateField(required=False, allow_null=True)

    def validate_center(self, value):
        centers = self.context.get("centers")
        if centers is None:
            raise PermissionDenied("Markaz konteksti topilmadi.")
        if not centers.filter(id=value).exists():
            raise PermissionDenied("Bu markaz sizga tegishli emas.")
        return value

    def validate_branch(self, value):
        if value is None:
            return value
        centers = self.context.get("centers")
        from apps.models import Branch

        if not Branch.objects.filter(id=value, center__in=centers).exists():
            raise PermissionDenied("Bu filial sizga tegishli emas.")
        return value

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
        center_id = validated_data.pop("center")
        branch_id = validated_data.pop("branch", None)
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
        teacher = Teacher.objects.create(
            user=user,
            branch_id=branch_id,
            specialization=validated_data.get("specialization", ""),
            experience=validated_data.get("experience", 0),
            salary=validated_data.get("salary"),
            bio=validated_data.get("bio", ""),
            date_of_birth=validated_data.get("date_of_birth"),
        )
        teacher.centers.set([center_id])
        return teacher

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
        if "branch" in validated_data:
            instance.branch_id = validated_data["branch"]
        if "center" in validated_data:
            instance.centers.set([validated_data["center"]])
        instance.save()
        return instance


class DirectorRoomSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "capacity", "branch", "center"]
        read_only_fields = ["center"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            centers = get_director_centers(user)
            self.fields["branch"].queryset = Branch.objects.filter(center__in=centers)


class DirectorCourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "description", "duration_months", "price", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class DirectorGroupStudentSerializer(ModelSerializer):
    student_name = SerializerMethodField()
    phone = SerializerMethodField()

    class Meta:
        model = GroupStudent
        fields = ["id", "student", "student_name", "phone", "joined_at", "is_active"]
        read_only_fields = ["id", "joined_at"]

    def get_student_name(self, obj):
        return obj.student.user.full_name if obj.student and obj.student.user else None

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
            "student_count",
            "room",
            "room_name",
            "status",
            "center",
            "branch",
            "start_date",
            "end_date",
            "lesson_days",
            "lesson_start_time",
            "lesson_end_time",
            "created_at",
            "updated_at",
        ]

    def get_teacher_name(self, obj):
        return obj.teacher.user.full_name if obj.teacher and obj.teacher.user else None


class DirectorGroupCreateSerializer(ModelSerializer):
    class Meta:
        model = Group
        exclude = ["center"]

    def validate(self, attrs):
        if attrs.get("lesson_start_time") and attrs.get("lesson_end_time"):
            if attrs["lesson_start_time"] >= attrs["lesson_end_time"]:
                raise ValidationError("Dars boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak.")
        return attrs

    def create(self, validated_data):
        validated_data["center"] = self.context["center"]
        return super().create(validated_data)


class DirectorGroupEnrollSerializer(Serializer):
    student_id = UUIDField()
    action = ChoiceField(choices=["add", "remove"])

    def validate(self, attrs):
        center = self.context.get("center")
        if not Student.objects.filter(id=attrs["student_id"], center=center).exists():
            raise ValidationError("Bu o'quvchi markazga tegishli emas.")
        return attrs

    def save(self):
        group = self.context["group"]
        student_id = self.validated_data["student_id"]
        if self.validated_data["action"] == "add":
            GroupStudent.objects.get_or_create(group=group, student_id=student_id)
        else:
            GroupStudent.objects.filter(group=group, student_id=student_id).delete()
        return group


class DirectorLessonListSerializer(ModelSerializer):
    group_name = CharField(source="group.name", read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "group", "group_name", "date", "start_time", "end_time", "topic", "notes"]
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
        group_id = validated_data.pop("group")
        return Lesson.objects.create(group_id=group_id, **validated_data)

    def update(self, instance, validated_data):
        group_id = validated_data.pop("group", None)
        if group_id is not None:
            instance.group_id = group_id
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
            return obj.student.user.full_name
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

    def validate(self, attrs):
        lesson = self.context["lesson"]
        student_ids = {rec["student"] for rec in attrs["records"]}

        valid_ids = set(
            Student.objects.filter(id__in=student_ids, center=lesson.group.center).values_list("id", flat=True)
        )
        invalid_ids = student_ids - valid_ids
        if invalid_ids:
            raise ValidationError("Ba'zi o'quvchilar bu markazga tegishli emas.")
        return attrs

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


class DirectorAdminListSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    branch_name = CharField(source="branch.name", read_only=True)

    class Meta:
        model = CenterStaff
        fields = ["id", "user", "center", "center_name", "branch", "branch_name", "notes", "created_at"]


class DirectorAdminDetailSerializer(ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    center_name = CharField(source="center.name", read_only=True)
    branch_name = CharField(source="branch.name", read_only=True)

    class Meta:
        model = CenterStaff
        fields = ["id", "user", "center", "center_name", "branch", "branch_name", "notes", "created_at"]


class DirectorAdminCreateSerializer(Serializer):
    phone = CharField(max_length=50, required=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    email = EmailField(required=False, allow_null=True)
    avatar = URLField(required=False, allow_null=True)
    password = CharField(write_only=True, required=False)
    center = UUIDField()
    branch = UUIDField(required=False, allow_null=True)
    notes = CharField(required=False, allow_blank=True)

    def validate_center(self, value):
        centers = self.context.get("centers")
        if centers is None:
            raise PermissionDenied("Markaz konteksti topilmadi.")
        if not centers.filter(id=value).exists():
            raise PermissionDenied("Bu markaz sizga tegishli emas.")
        return value

    def validate_branch(self, value):
        if value is None:
            return value
        centers = self.context.get("centers")
        from apps.models import Branch

        if not Branch.objects.filter(id=value, center__in=centers).exists():
            raise PermissionDenied("Bu filial sizga tegishli emas.")
        return value

    def validate_phone(self, value):
        normalized = normalize_phone(value)
        qs = User.objects.filter(phone=normalized)
        if self.instance:
            qs = qs.exclude(id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("Bu telefon raqam allaqachon mavjud.")
        return value

    def validate_branch_is_centers(self, attrs):
        center_id = attrs.get("center")
        branch_id = attrs.get("branch")

        if center_id and branch_id:
            if not Branch.objects.filter(id=branch_id, center_id=center_id).exists():
                raise ValidationError({"branch": "Tanlangan filial ushbu o'quv markaziga tegishli emas!"})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        center_id = validated_data.pop("center")
        branch_id = validated_data.pop("branch", None)
        password = validated_data.pop("password", None)
        notes = validated_data.pop("notes", "")

        user = User.objects.create_user(
            phone=validated_data["phone"],
            password=password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data.get("email"),
            avatar=validated_data.get("avatar"),
            role=User.Role.ADMIN,
        )
        return CenterStaff.objects.create(
            user=user,
            center_id=center_id,
            branch_id=branch_id,
            notes=notes,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        user = instance.user

        if "phone" in validated_data:
            user.phone = normalize_phone(validated_data["phone"])

        for field in ["first_name", "last_name", "email", "avatar"]:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()

        if "notes" in validated_data:
            instance.notes = validated_data["notes"]
        if "center" in validated_data:
            instance.center_id = validated_data["center"]
        if "branch" in validated_data:
            instance.branch_id = validated_data["branch"]

        instance.save()
        return instance
