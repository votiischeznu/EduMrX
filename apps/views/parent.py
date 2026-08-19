from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Payment
from apps.permissions import IsParent
from apps.serializers import ParentDashboardSerializer, ParentPaymentInitiateSerializer
from apps.service import ClickPaymentService


@extend_schema(tags=["ParentDashboard"])
class ParentDashboardView(APIView):
    permission_classes = [IsParent]

    def get(self, request):
        parent = getattr(request.user, "parent_profile", None)
        if not parent:
            return Response({"detail": "Ota-ona profili topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ParentDashboardSerializer(parent)
        return Response(serializer.data)


@extend_schema(tags=["ParentPayment"])
class ParentPaymentInitiateView(APIView):
    permission_classes = [IsParent]

    @extend_schema(
        request=ParentPaymentInitiateSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        parent = getattr(request.user, "parent_profile", None)
        if not parent:
            return Response({"detail": "Ota-ona profili topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ParentPaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = Payment.objects.filter(id=serializer.validated_data["payment_id"], student__parent=parent).first()

        if not payment:
            return Response({"detail": "To'lov topilmadi yoki sizga tegishli emas."}, status=status.HTTP_404_NOT_FOUND)

        if payment.status not in [Payment.Status.PENDING, Payment.Status.OVERDUE]:
            return Response({"detail": "Bu to'lov allaqachon yopilgan."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pay_url = ClickPaymentService().create_payment_link(payment)
            return Response({"payment_url": pay_url}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
