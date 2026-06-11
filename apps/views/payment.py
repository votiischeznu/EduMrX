from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions import IsSuperAdmin
from apps.service import (
    FinanceService,
    FinanceChartService,
    FinanceCentersService,
    FinanceTransactionsService,
)


@extend_schema(tags=["SuperAdminFinance"])
class SuperAdminFinanceSummaryView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        data = FinanceService.get_summary_data()
        return Response({"data": data})




@extend_schema(tags=["SuperAdminFinance"])
class SuperAdminFinanceChartView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        period = request.query_params.get("period", "month")
        data = FinanceChartService.get_chart_data(period)
        return Response({"data": data})



@extend_schema(tags=["SuperAdminFinance"])
class SuperAdminFinanceCentersView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        status = request.query_params.get("status", "all")
        search = request.query_params.get("search", "")
        sort_by = request.query_params.get("sort_by", "month_revenue")
        sort_dir = request.query_params.get("sort_dir", "desc")
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 20))

        data, total, total_sum = FinanceCentersService.get_centers_finance_list(
            status, search, sort_by, sort_dir, page, per_page
        )

        return Response(
            {
                "data": data,
                "meta": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_revenue_sum": total_sum,
                },
            }
        )



@extend_schema(tags=["SuperAdminFinance"])
class SuperAdminFinanceTransactionsView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 20))

        data, total = FinanceTransactionsService.get_transactions_list(page, per_page)

        return Response(
            {"data": data, "meta": {"total": total, "page": page, "per_page": per_page}}
        )
