from django.contrib.auth import update_session_auth_hash
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import User
from apps.serializers import StudentProfileSerializer, TeacherProfileSerializer, AdminProfileSerializer
from apps.serializers.profile_serializers import PasswordChangeSerializer


class MyProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        role = self.request.user.role

        if role == User.Role.STUDENT:
            return StudentProfileSerializer

        elif role == User.Role.TEACHER:
            return TeacherProfileSerializer

        return AdminProfileSerializer

    def get_object(self):
        return self.request.user



class PasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        update_session_auth_hash(request, user)

        return Response({
            'message': "Parol muvaffaqiyatli uzgartirildi"})