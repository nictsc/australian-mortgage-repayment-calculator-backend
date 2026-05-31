from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SavedScenario, LoanSplit
from .serializers import (
    CalculatorInputSerializer,
    CalculatorResultSerializer,
    SavedScenarioSerializer,
    LoanSplitSerializer,
)
from .services import MortgageCalculatorService


class CalculateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary='Calculate mortgage repayments',
        request=CalculatorInputSerializer,
        responses={200: CalculatorResultSerializer},
    )
    def post(self, request):
        serializer = CalculatorInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = MortgageCalculatorService.calculate(
            loan_amount=float(data['loan_amount']),
            annual_rate=float(data['annual_rate']),
            rate_type=data['rate_type'],
            repayment_type=data['repayment_type'],
            frequency=data['repayment_frequency'],
            loan_term_years=data['loan_term_years'],
            fixed_rate_period_years=data.get('fixed_rate_period_years'),
            revert_rate=float(data['revert_rate']) if data.get('revert_rate') else None,
            offset_amount=float(data.get('offset_amount', 0)),
            rate_change_step=float(data.get('rate_change_step', 0.25)),
        )

        return Response(result, status=status.HTTP_200_OK)


class SavedScenarioViewSet(viewsets.ModelViewSet):
    serializer_class = SavedScenarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedScenario.objects.filter(user=self.request.user).prefetch_related('splits')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(summary='List saved scenarios')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary='Create and save a scenario')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary='Retrieve a saved scenario')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary='Update a saved scenario')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary='Partially update a saved scenario')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary='Delete a saved scenario')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
