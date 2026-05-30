from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, BooleanField, CharField, ImageField
from rest_framework.serializers import ModelSerializer

from apps.models import Room, Group, GroupStudent, Teacher


class RoomModelSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'capacity']


class TeacherShortProfileSerializer(ModelSerializer):
    full_name = CharField(source='user.full_name', read_only=True)
    phone = CharField(source='user.phone', read_only=True)
    avatar = ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = Teacher
        fields = ['id', 'full_name', 'phone', 'avatar']


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
            representation['teacher'] = TeacherShortProfileSerializer(instance.teacher.user, context=self.context).data

        if instance.room:
            representation['room'] = RoomModelSerializer(instance.room, context=self.context).data

        return representation


class GroupStudentModelSerializer(ModelSerializer):
    class Meta:
        model = GroupStudent
        fields = 'id', 'group', 'student', 'joined_at', 'is_active'

    def validate(self, attrs):
        group = attrs.get('group')
        if not self.instance and group and group.is_full:
            raise ValidationError("Bu guruhda bo'sh joy qolmagan")
        return attrs
