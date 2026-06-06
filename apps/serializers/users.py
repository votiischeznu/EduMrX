from rest_framework.serializers import ModelSerializer

from apps.models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'password', 'first_name', 'last_name', 'role', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
