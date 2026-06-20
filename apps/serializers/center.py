from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    FloatField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from apps.models.centers import Branch
from apps.models.groups import Room


class BranchRoomSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "capacity"]


class BranchListSerializer(ModelSerializer):
    coordinates = SerializerMethodField()
    manager = SerializerMethodField()
    stats = SerializerMethodField()

    class Meta:
        model = Branch
        fields = ["id", "name", "status", "address", "phone", "coordinates", "manager", "stats", "created_at"]

    def get_coordinates(self, obj):
        return obj.coordinates

    def get_manager(self, obj):
        if not obj.manager_id:
            return None
        return {
            "id": obj.manager.id,
            "first_name": obj.manager.first_name,
            "last_name": obj.manager.last_name,
            "phone": obj.manager.phone,
        }

    def get_stats(self, obj):
        return {
            "students_count": obj.students_count,
            "teachers_count": obj.teachers_count,
            "rooms_count": obj.rooms_count,
        }


class BranchDetailSerializer(BranchListSerializer):
    rooms = BranchRoomSerializer(many=True, read_only=True)
    manager_id = SerializerMethodField()

    class Meta(BranchListSerializer.Meta):
        fields = BranchListSerializer.Meta.fields + ["manager_id", "rooms"]

    def get_manager_id(self, obj):
        return obj.manager_id


class BranchCreateUpdateSerializer(Serializer):
    name = CharField(max_length=255, required=False)
    address = CharField(required=False)
    phone = CharField(max_length=50, required=False)
    coordinates = ListField(child=FloatField(), min_length=2, max_length=2, required=False)
    status = ChoiceField(choices=Branch.Status.choices, required=False)

    def validate(self, attrs):
        if "manager" in self.initial_data or "manager_id" in self.initial_data:
            raise ValidationError(
                "manager_id ushbu endpoint orqali o'zgartirilmaydi. Biriktirish keyingi bosqichda alohida endpoint orqali amalga oshiriladi."
            )
        if self.instance is None:
            for required_field in ["name", "address", "phone", "coordinates"]:
                if required_field not in attrs:
                    raise ValidationError({required_field: "Bu maydon majburiy."})
        return attrs

    def create(self, validated_data):
        center = self.context["center"]

        limit = center.effective_branch_limit
        if limit is not None and center.branches.exclude(status=Branch.Status.ARCHIVED).count() >= limit:
            raise PermissionDenied(
                {"error": "BRANCH_LIMIT_EXCEEDED", "message": "Tarif rejangizdagi filiallar limiti tugagan."}
            )

        lat, lng = validated_data.pop("coordinates")
        return Branch.objects.create(
            center=center,
            latitude=lat,
            longitude=lng,
            **validated_data,
        )

    def update(self, instance, validated_data):
        coords = validated_data.pop("coordinates", None)
        if coords:
            instance.latitude, instance.longitude = coords
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
