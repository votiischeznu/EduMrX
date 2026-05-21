from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DateField, DateTimeField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models import User


class PasswordChangeSerializer(Serializer):
    old_password = CharField(write_only=True)
    new_password = CharField(write_only=True, min_length=8)
    confirm_password = CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user

        if not user.check_password(value):
            raise ValidationError({
                'old_password': "Joriy parol noto'g'ri"
            })

        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise ValidationError({
                'confirm_password': "Parollar mos emas"
            })

        validate_password(
            password=new_password,
            user=self.context['request'].user
        )
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user

        user.set_password(
            self.validated_data['new_password']
        )
        user.save(update_fields=['password'])
        return user


class BaseUserProfileModelSerializer(ModelSerializer):
    full_name = CharField(read_only=True)

    class Meta:
        model = User

        fields = ['id', 'phone', 'email', 'first_name', 'last_name', 'full_name', 'role', 'avatar', ]

        extra_kwargs = {
            'id': {'read_only': True},
            'phone': {'read_only': True},
            'role': {'read_only': True},
        }

    def validate_first_name(self, value):
        if not value.strip():
            raise ValidationError("Ism bo'sh bo'lmasligi kerak")
        return value.strip()

    def validate_last_name(self, value):
        if not value.strip():
            raise ValidationError("Familiya bo'sh bo'lmasligi kerak")
        return value.strip()

    def validate_email(self, value):
        if not value:
            return value

        qs = User.objects.filter(email=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(
                "Bu email allaqachon ro'yxatdan o'tgan"
            )

        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if avatar is not None:

            if instance.avatar:
                instance.avatar.delete(save=False)
            instance.avatar = avatar
        instance.save()
        return instance


class AdminProfileSerializer(BaseUserProfileModelSerializer):
    class Meta(BaseUserProfileModelSerializer.Meta):
        fields = (BaseUserProfileModelSerializer.Meta.fields + ['is_active', 'is_staff', ])
        extra_kwargs = {
            **BaseUserProfileModelSerializer.Meta.extra_kwargs,
            'is_staff': {'read_only': True},
            'is_active': {'read_only': True}
        }


class TeacherProfileSerializer(BaseUserProfileModelSerializer):
    class Meta(BaseUserProfileModelSerializer.Meta):
        pass


class StudentProfileSerializer(BaseUserProfileModelSerializer):
    date_of_birth = DateField(source='student_profile.date_of_birth', required=False, allow_null=True, )
    address = CharField(source='student_profile.address', required=False, allow_blank=True, )
    status = CharField(source='student_profile.status', read_only=True, )
    enrolled_at = DateTimeField(source='student_profile.enrolled_at', read_only=True, )

    class Meta(BaseUserProfileModelSerializer.Meta):
        model = User
        fields = (BaseUserProfileModelSerializer.Meta.fields + ['date_of_birth', 'address', 'status', 'enrolled_at'])
        extra_kwargs = {
            **BaseUserProfileModelSerializer.Meta.extra_kwargs,
            'status': {'read_only': True},
            'enrolled_at': {'read_only': True},
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        student_data = validated_data.pop(
            'student_profile',
            {}
        )

        instance = super().update(
            instance,
            validated_data
        )

        student = instance.student_profile
        for attr, value in student_data.items():
            setattr(student, attr, value)
        student.save()

        return instance
