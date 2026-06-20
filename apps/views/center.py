from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.models.centers import Branch
from apps.models.groups import  Group
from apps.models.payments import Debt
from apps.permissions import IsDirector
from apps.serializers.center import BranchListSerializer, BranchDetailSerializer, BranchCreateUpdateSerializer
from apps.views.director import get_single_center_or_404


@extend_schema_view(
    get=extend_schema(tags=["4. Director — Branches"]),
    post=extend_schema(tags=["4. Director — Branches"]),
)
class BranchListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "address"]

    def get_queryset(self):
        center = get_single_center_or_404(self.request.user)
        qs = Branch.objects.filter(center=center).exclude(status=Branch.Status.ARCHIVED)
        status_param = self.request.query_params.get("status")
        if status_param and status_param != "all":
            qs = qs.filter(status=status_param)
        return qs.order_by("-created_at")

    def get_serializer_class(self):
        return BranchCreateUpdateSerializer if self.request.method == "POST" else BranchListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        return Response(
            {
                "status": "success",
                "message": "Filial muvaffaqiyatli yaratildi",
                "data": BranchListSerializer(branch).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = BranchListSerializer(qs, many=True)
        return Response({"status": "success", "count": qs.count(), "data": serializer.data})


@extend_schema_view(
    get=extend_schema(tags=["4. Director — Branches"]),
    patch=extend_schema(tags=["4. Director — Branches"]),
    delete=extend_schema(tags=["4. Director — Branches"]),
)
class BranchDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        center = get_single_center_or_404(self.request.user)
        return Branch.objects.filter(center=center)

    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs["pk"])
        except Branch.DoesNotExist:
            raise NotFound("Filial topilmadi.")

    def get_serializer_class(self):
        return BranchCreateUpdateSerializer if self.request.method == "PATCH" else BranchDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["center"] = get_single_center_or_404(self.request.user)
        return context

    def retrieve(self, request, *args, **kwargs):
        branch = self.get_object()
        return Response({"status": "success", "data": BranchDetailSerializer(branch).data})

    def partial_update(self, request, *args, **kwargs):
        branch = self.get_object()
        serializer = self.get_serializer(branch, data=request.data, partial=True, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        return Response(
            {
                "status": "success",
                "message": "Filial muvaffaqiyatli yangilandi",
                "data": BranchListSerializer(branch).data,
            }
        )

    def destroy(self, request, *args, **kwargs):
        branch = self.get_object()

        has_active_groups = Group.objects.filter(branch=branch, status=Group.Status.ACTIVE).exists()
        has_debt = Debt.objects.filter(
            student__branch=branch,
            status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID],
        ).exists()

        if has_active_groups or has_debt:
            raise ValidationError(
                {
                    "error": "BRANCH_HAS_ACTIVE_DATA",
                    "message": "Ushbu filialni o'chira olmaysiz. Filialda faol guruhlar yoki yopilmagan kassa mavjud. Avval ularni boshqa filialga ko'chiring.",
                }
            )

        branch.status = Branch.Status.ARCHIVED
        branch.save(update_fields=["status", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)