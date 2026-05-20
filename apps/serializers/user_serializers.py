from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from apps.models import User


class UserModelSerializer(ModelSerializer):
    full_name = CharField(read_only=True)
    password = CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'avatar', 'is_active', 'password'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
