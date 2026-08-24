from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, CharField
from rest_framework.serializers import ModelSerializer

from apps.models import Payment, Debt
from apps.models.payments import Expense, ExpenseCategory


class PaymentListSerializer(ModelSerializer):
    student_name = SerializerMethodField()
    student_phone = CharField(source="student.phone", read_only=True)
    group_name = CharField(source="group.name", read_only=True)
    branch_name = CharField(source="branch.name", read_only=True)
    status_display = CharField(source="get_status_display", read_only=True)
    method_display = CharField(source="get_method_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "student",
            "student_name",
            "student_phone",
            "group",
            "group_name",
            "branch",
            "branch_name",
            "amount",
            "discount",
            "final_amount",
            "method",
            "method_display",
            "status",
            "status_display",
            "period_month",
            "period_year",
            "due_date",
            "paid_at",
        ]

    def get_student_name(self, obj):
        user = obj.student.user
        if not user:
            return ""
        return f"{user.first_name} {user.last_name}".strip() or user.phone


class PaymentDetailSerializer(PaymentListSerializer):
    class Meta(PaymentListSerializer.Meta):
        fields = PaymentListSerializer.Meta.fields + ["receipt_number", "comment", "created_at", "updated_at"]


class PaymentCreateSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "student",
            "group",
            "branch",
            "amount",
            "discount",
            "method",
            "status",
            "period_month",
            "period_year",
            "due_date",
            "receipt_number",
            "comment",
        ]
        read_only_fields = ["id"]

    def validate_student(self, student):
        center = self.context["center"]
        if student.center_id != center.id:
            raise ValidationError("Bu o'quvchi sizning markazingizga tegishli emas.")
        return student

    def validate_group(self, group):
        center = self.context["center"]
        if group and group.branch.center_id != center.id:
            raise ValidationError("Bu guruh sizning markazingizga tegishli emas.")
        return group

    def validate_branch(self, branch):
        center = self.context["center"]
        if branch and branch.center_id != center.id:
            raise ValidationError("Bu filial sizning markazingizga tegishli emas.")
        return branch

    def validate_discount(self, value):
        if value < 0:
            raise ValidationError("Chegirma manfiy bo'lishi mumkin emas.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError("Summa 0 dan katta bo'lishi kerak.")
        return value

    def validate_period_month(self, value):
        if not (1 <= value <= 12):
            raise ValidationError("Oy 1 dan 12 gacha bo'lishi kerak.")
        return value

    def validate(self, attrs):
        amount = attrs.get("amount", 0)
        discount = attrs.get("discount", 0)
        if discount > amount:
            raise ValidationError({"discount": "Chegirma summadan katta bo'lishi mumkin emas."})
        return attrs


class PaymentUpdateSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = ["discount", "method", "status", "due_date", "receipt_number", "comment"]

    def validate_discount(self, value):
        if value < 0:
            raise ValidationError("Chegirma manfiy bo'lishi mumkin emas.")
        instance = self.instance
        if instance and value > instance.amount:
            raise ValidationError("Chegirma summadan katta bo'lishi mumkin emas.")
        return value


class DebtListSerializer(ModelSerializer):
    student_name = SerializerMethodField()
    student_phone = CharField(source="student.phone", read_only=True)
    group_name = CharField(source="group.name", read_only=True)
    status_display = CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Debt
        fields = [
            "id",
            "student",
            "student_name",
            "student_phone",
            "group",
            "group_name",
            "amount",
            "due_date",
            "status",
            "status_display",
        ]

    def get_student_name(self, obj):
        user = obj.student.user
        return f"{user.first_name} {user.last_name}".strip()


class DebtCreateSerializer(ModelSerializer):
    class Meta:
        model = Debt
        fields = ["id", "student", "group", "amount", "due_date", "status"]
        read_only_fields = ["id"]

    def validate_student(self, student):
        center = self.context["center"]
        if student.center_id != center.id:
            raise ValidationError("Bu o'quvchi sizning markazingizga tegishli emas.")
        return student

    def validate_group(self, group):
        center = self.context["center"]
        if group.branch.center_id != center.id:
            raise ValidationError("Bu guruh sizning markazingizga tegishli emas.")
        return group

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError("Summa 0 dan katta bo'lishi kerak.")
        return value


class ExpenseCategorySerializer(ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "name", "icon", "is_system", "is_active"]
        read_only_fields = ["id", "is_system"]


class ExpenseCategoryCreateSerializer(ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "name", "icon"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        center = self.context["center"]
        qs = ExpenseCategory.objects.filter(center=center, name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Bu nomli kategoriya allaqachon mavjud.")
        return value

    def create(self, validated_data):
        validated_data["center"] = self.context["center"]
        return super().create(validated_data)


class ExpenseListSerializer(ModelSerializer):
    category_name = CharField(source="category.name", read_only=True)
    branch_name = CharField(source="branch.name", read_only=True)
    performed_by_name = SerializerMethodField()
    status_display = CharField(source="get_status_display", read_only=True)
    method_display = CharField(source="get_method_display", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "title",
            "amount",
            "method",
            "method_display",
            "status",
            "status_display",
            "category",
            "category_name",
            "branch",
            "branch_name",
            "expense_date",
            "period_month",
            "period_year",
            "performed_by_name",
        ]

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            full_name = f"{obj.performed_by.first_name} {obj.performed_by.last_name}".strip()
            return full_name or obj.performed_by.phone
        return None


class ExpenseDetailSerializer(ExpenseListSerializer):
    class Meta(ExpenseListSerializer.Meta):
        fields = ExpenseListSerializer.Meta.fields + ["paid_at", "receipt_image", "comment", "created_at", "updated_at"]


class ExpenseCreateSerializer(ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            "id",
            "title",
            "amount",
            "method",
            "status",
            "category",
            "branch",
            "expense_date",
            "period_month",
            "period_year",
            "receipt_image",
            "comment",
        ]
        read_only_fields = ["id"]

    def validate_branch(self, branch):
        center = self.context["center"]
        if branch and branch.center_id != center.id:
            raise ValidationError("Bu filial sizning markazingizga tegishli emas.")
        return branch

    def validate_category(self, category):
        center = self.context["center"]
        if category and not category.is_system and category.center_id != center.id:
            raise ValidationError("Bu kategoriya sizning markazingizga tegishli emas.")
        return category

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError("Summa 0 dan katta bo'lishi kerak.")
        return value

    def create(self, validated_data):
        validated_data["center"] = self.context["center"]
        validated_data["performed_by"] = self.context["request"].user
        return super().create(validated_data)


class ExpenseUpdateSerializer(ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            "title",
            "amount",
            "method",
            "status",
            "category",
            "branch",
            "expense_date",
            "period_month",
            "period_year",
            "receipt_image",
            "comment",
        ]

    def validate_branch(self, branch):
        center = self.context["center"]
        if branch and branch.center_id != center.id:
            raise ValidationError("Bu filial sizning markazingizga tegishli emas.")
        return branch

    def validate_category(self, category):
        center = self.context["center"]
        if category and not category.is_system and category.center_id != center.id:
            raise ValidationError("Bu kategoriya sizning markazingizga tegishli emas.")
        return category

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError("Summa 0 dan katta bo'lishi kerak.")
        return value
