from django.db.models import Sum, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
    DestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Payment, Debt, Center
from apps.models.payments import ExpenseCategory, Expense
from apps.permissions import IsDirector
from apps.serializers.finance import (
    PaymentListSerializer,
    PaymentDetailSerializer,
    PaymentCreateSerializer,
    PaymentUpdateSerializer,
    DebtListSerializer,
    DebtCreateSerializer,
    ExpenseCategorySerializer,
    ExpenseCategoryCreateSerializer,
    ExpenseListSerializer,
    ExpenseDetailSerializer,
    ExpenseCreateSerializer,
    ExpenseUpdateSerializer,
)


def get_director_center(request):
    center_id = request.query_params.get("center_id")
    qs = Center.objects.filter(director=request.user, is_deleted=False)
    if center_id:
        return qs.filter(id=center_id).first()
    return qs.first()


class PaymentListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["branch", "group", "student", "status", "method", "period_month", "period_year"]
    search_fields = ["student__first_name", "student__last_name", "student__phone", "receipt_number"]
    ordering_fields = ["due_date", "paid_at", "final_amount", "created_at"]
    ordering = ["-created_at"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        return (
            Payment.objects.filter(student__center=center)
            .select_related("student", "group", "branch")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PaymentCreateSerializer
        return PaymentListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = self.get_center()
        return ctx

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        totals = qs.aggregate(
            total_amount=Sum("final_amount"),
            paid_total=Sum("final_amount", filter=Q(status=Payment.Status.PAID)),
            pending_total=Sum("final_amount", filter=Q(status=Payment.Status.PENDING)),
            overdue_total=Sum("final_amount", filter=Q(status=Payment.Status.OVERDUE)),
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data.update(
                {
                    "total_amount": totals["total_amount"] or 0,
                    "paid_total": totals["paid_total"] or 0,
                    "pending_total": totals["pending_total"] or 0,
                    "overdue_total": totals["overdue_total"] or 0,
                }
            )
            return response

        serializer = self.get_serializer(qs, many=True)
        return Response({"results": serializer.data, **{k: v or 0 for k, v in totals.items()}})


class PaymentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        return Payment.objects.filter(student__center=center).select_related("student", "group", "branch")

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return PaymentUpdateSerializer
        return PaymentDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = self.get_center()
        return ctx

    def perform_destroy(self, instance):
        if instance.status == Payment.Status.PAID:
            instance.status = Payment.Status.REFUNDED
            instance.save(update_fields=["status"])
        else:
            instance.status = Payment.Status.CANCELLED
            instance.save(update_fields=["status"])


class StudentPaymentListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    serializer_class = PaymentListSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "method", "period_month", "period_year"]
    ordering = ["-created_at"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        student_id = self.kwargs["student_id"]
        return (
            Payment.objects.filter(
                student__center=center,
                student_id=student_id,
            )
            .select_related("student", "group", "branch")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        totals = qs.aggregate(
            total_paid=Sum("final_amount", filter=Q(status=Payment.Status.PAID)),
            total_debt=Sum("final_amount", filter=Q(status=Payment.Status.OVERDUE)),
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data.update(
                {
                    "total_paid": totals["total_paid"] or 0,
                    "total_debt": totals["total_debt"] or 0,
                }
            )
            return response

        serializer = self.get_serializer(qs, many=True)
        return Response(
            {
                "results": serializer.data,
                "total_paid": totals["total_paid"] or 0,
                "total_debt": totals["total_debt"] or 0,
            }
        )


class PaymentSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def get(self, request):
        center = get_director_center(request)
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        qs = Payment.objects.filter(student__center=center)
        if year:
            qs = qs.filter(period_year=year)
        if month:
            qs = qs.filter(period_month=month)

        totals = qs.aggregate(
            total=Sum("final_amount"),
            paid=Sum("final_amount", filter=Q(status=Payment.Status.PAID)),
            pending=Sum("final_amount", filter=Q(status=Payment.Status.PENDING)),
            overdue=Sum("final_amount", filter=Q(status=Payment.Status.OVERDUE)),
            refunded=Sum("final_amount", filter=Q(status=Payment.Status.REFUNDED)),
            count_total=Count("id"),
            count_paid=Count("id", filter=Q(status=Payment.Status.PAID)),
            count_overdue=Count("id", filter=Q(status=Payment.Status.OVERDUE)),
        )

        by_method = (
            qs.filter(status=Payment.Status.PAID)
            .values("method")
            .annotate(total=Sum("final_amount"), count=Count("id"))
            .order_by("-total")
        )

        by_branch = (
            qs.values("branch__name")
            .annotate(
                total=Sum("final_amount"),
                paid=Sum("final_amount", filter=Q(status=Payment.Status.PAID)),
            )
            .order_by("-total")
        )

        monthly = []
        if year and not month:
            monthly = (
                qs.values("period_month")
                .annotate(
                    total=Sum("final_amount"),
                    paid=Sum("final_amount", filter=Q(status=Payment.Status.PAID)),
                )
                .order_by("period_month")
            )

        return Response(
            {
                "totals": {k: v or 0 for k, v in totals.items()},
                "by_method": list(by_method),
                "by_branch": list(by_branch),
                "monthly": list(monthly),
            }
        )


class DebtListCreateView(ListCreateAPIView):    
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "group", "student"]
    search_fields = ["student__first_name", "student__last_name", "student__phone"]
    ordering_fields = ["due_date", "amount"]
    ordering = ["due_date"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        return Debt.objects.filter(student__center=center).select_related("student", "group").order_by("due_date")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DebtCreateSerializer
        return DebtListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = self.get_center()
        return ctx

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        total_debt = (
            qs.filter(status__in=[Debt.Status.UNPAID, Debt.Status.PARTIALLY_PAID]).aggregate(total=Sum("amount"))[
                "total"
            ]
            or 0
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["total_debt"] = total_debt
            return response

        serializer = self.get_serializer(qs, many=True)
        return Response({"results": serializer.data, "total_debt": total_debt})


def get_director_center(request):
    center_id = request.query_params.get("center_id")
    qs = Center.objects.filter(director=request.user, is_deleted=False)
    if center_id:
        return qs.filter(id=center_id).first()
    return qs.first()


class ExpenseCategoryListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        # Tizim kategoriyalari + shu markazning o'z kategoriyalari
        return ExpenseCategory.objects.filter(
            Q(is_system=True) | Q(center=center),
            is_active=True,
        ).order_by("name")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ExpenseCategoryCreateSerializer
        return ExpenseCategorySerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = self.get_center()
        return ctx


class ExpenseCategoryDetailView(RetrieveUpdateAPIView, DestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        return ExpenseCategory.objects.filter(Q(is_system=True) | Q(center=center))

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return ExpenseCategoryCreateSerializer
        return ExpenseCategorySerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = self.get_center()
        return ctx

    def perform_destroy(self, instance):
        if instance.is_system:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Tizim kategoriyasini o'chirib bo'lmaydi.")
        # Soft delete
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class ExpenseListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["branch", "category", "status", "method", "period_month", "period_year"]
    search_fields = ["title", "comment"]
    ordering_fields = ["expense_date", "amount", "created_at"]
    ordering = ["-expense_date"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        return (
            Expense.objects.filter(center=center)
            .select_related("category", "branch", "performed_by")
            .order_by("-expense_date", "-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ExpenseCreateSerializer
        return ExpenseListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = self.get_center()
        return ctx

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        total = qs.aggregate(total=Sum("amount"))["total"] or 0

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["total_amount"] = total
            return response

        serializer = self.get_serializer(qs, many=True)
        return Response({"results": serializer.data, "total_amount": total})


class ExpenseDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsDirector]
    http_method_names = ["get", "patch", "delete"]

    def get_center(self):
        return get_director_center(self.request)

    def get_queryset(self):
        center = self.get_center()
        return Expense.objects.filter(center=center).select_related("category", "branch", "performed_by")

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return ExpenseUpdateSerializer
        return ExpenseDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["center"] = self.get_center()
        return ctx

    def perform_destroy(self, instance):
        if instance.status == Expense.Status.PAID:
            instance.status = Expense.Status.CANCELLED
            instance.save(update_fields=["status"])
        else:
            instance.delete()


class ExpenseSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsDirector]

    def get(self, request):
        center = get_director_center(request)
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        qs = Expense.objects.filter(center=center)
        if year:
            qs = qs.filter(period_year=year)
        if month:
            qs = qs.filter(period_month=month)

        from django.db.models import Count

        by_category = (
            qs.values("category__name", "category__icon")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        by_status = qs.values("status").annotate(total=Sum("amount"), count=Count("id"))

        by_branch = qs.values("branch__name").annotate(total=Sum("amount"), count=Count("id")).order_by("-total")

        grand_total = qs.aggregate(total=Sum("amount"))["total"] or 0

        return Response(
            {
                "grand_total": grand_total,
                "by_category": list(by_category),
                "by_status": list(by_status),
                "by_branch": list(by_branch),
            }
        )
