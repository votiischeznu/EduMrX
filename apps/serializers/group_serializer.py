from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, BooleanField
from rest_framework.serializers import ModelSerializer

from apps.models import Room, Group, GroupStudent
from apps.serializers.profile_serializers import TeacherProfileSerializer
from apps.serializers.profile_serializers import BaseUserProfileModelSerializer


class RoomModelSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = 'id', 'name', 'capacity'


class TeacherShortProfileSerializer(BaseUserProfileModelSerializer):
    class Meta(BaseUserProfileModelSerializer.Meta):
        fields = 'id', 'full_name', 'phone', 'avatar'


class GroupModelSerializer(ModelSerializer):
    student_count = IntegerField(read_only=True)
    capacity = IntegerField(read_only=True)
    is_full = BooleanField(read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'course', 'teacher', 'room', 'status',
                  'start_date', 'end_date', 'lesson_days', 'lesson_start_time',
                  'lesson_end_time', 'student_count', 'capacity', 'is_full')

        extra_kwargs = {
            'id': {'read_only': True}
        }

    def validate(self, attrs):
        instance = Group(**attrs)
        try:
            instance.clean()
        except ValidationError as e:
            raise ValidationError(e.message_dict)
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.teacher:
            representation['teacher'] = TeacherShortProfileSerializer(instance.teacher, context=self.context).data

        if instance.room:
            representation['room'] = RoomModelSerializer(instance.room, context=self.context).data

        return representation


class GroupStudentModelSerializer(ModelSerializer):
    class Meta:
        model = GroupStudent
        fields = 'id', 'group', 'student', 'joined_at', 'is_active'

    def validate(self, attrs):
        group = attrs.get('group')
        if group.is_full:
            raise ValidationError("Bu gruhda bo'sh joy qolmagan(Xona sig'imi to'lgan)")
        return attrs
