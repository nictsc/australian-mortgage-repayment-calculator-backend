from decimal import Decimal
from rest_framework import serializers

from .models import SavedScenario, LoanSplit
from .services import MortgageCalculatorService


class CalculatorInputSerializer(serializers.Serializer):
    loan_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('1.00')
    )
    annual_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('20.00')
    )
    rate_type = serializers.ChoiceField(choices=['variable', 'fixed'])
    repayment_type = serializers.ChoiceField(choices=['principal_and_interest', 'interest_only'])
    repayment_frequency = serializers.ChoiceField(choices=['weekly', 'fortnightly', 'monthly'])
    loan_term_years = serializers.IntegerField(min_value=1, max_value=40)
    fixed_rate_period_years = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    revert_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('20.00'),
        required=False, allow_null=True
    )
    offset_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('0.00'), default=Decimal('0.00')
    )
    rate_change_step = serializers.DecimalField(
        max_digits=3, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('5.00'),
        default=Decimal('0.25')
    )

    def validate(self, data):
        if data['rate_type'] == 'fixed':
            if not data.get('fixed_rate_period_years'):
                raise serializers.ValidationError(
                    'fixed_rate_period_years is required for fixed rate loans.'
                )
            if not data.get('revert_rate'):
                raise serializers.ValidationError(
                    'revert_rate is required for fixed rate loans.'
                )

        if data.get('repayment_type') == 'interest_only':
            if not data.get('fixed_rate_period_years'):
                raise serializers.ValidationError(
                    'fixed_rate_period_years is required for interest only loans.'
                )
            if not data.get('revert_rate'):
                raise serializers.ValidationError(
                    'revert_rate is required for interest only loans.'
                )

        offset_amount = data.get('offset_amount', Decimal('0'))
        if offset_amount > Decimal('0'):
            if data['rate_type'] != 'variable':
                raise serializers.ValidationError(
                    'Offset accounts can only be attached to variable rate loans.'
                )
            if offset_amount > data['loan_amount']:
                raise serializers.ValidationError(
                    'Offset amount cannot exceed loan amount.'
                )

        return data


class CalculatorResultSerializer(serializers.Serializer):
    loan_amount = serializers.CharField()
    annual_rate = serializers.FloatField()
    rate_type = serializers.CharField()
    repayment_type = serializers.CharField()
    repayment_frequency = serializers.CharField()
    loan_term_years = serializers.IntegerField()
    fixed_rate_period_years = serializers.IntegerField(allow_null=True)
    revert_rate = serializers.FloatField(allow_null=True)
    offset_amount = serializers.CharField()
    repayment_amount = serializers.CharField()
    total_repayment = serializers.CharField()
    total_interest = serializers.CharField()
    offset_savings = serializers.JSONField(allow_null=True)
    rate_change_step = serializers.FloatField()
    rate_sensitivity = serializers.JSONField()
    schedule = serializers.ListField()


class LoanSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanSplit
        fields = [
            'id', 'order', 'loan_amount', 'annual_rate', 'rate_type',
            'repayment_type', 'repayment_frequency', 'loan_term_years',
            'fixed_rate_period_years', 'revert_rate', 'offset_amount',
            'repayment_amount', 'total_interest', 'total_repayment',
        ]
        read_only_fields = ['id', 'repayment_amount', 'total_interest', 'total_repayment']

    def validate(self, data):
        if data['rate_type'] == 'fixed':
            if not data.get('fixed_rate_period_years'):
                raise serializers.ValidationError(
                    'fixed_rate_period_years is required for fixed rate loans.'
                )
            if not data.get('revert_rate'):
                raise serializers.ValidationError(
                    'revert_rate is required for fixed rate loans.'
                )

        if data.get('repayment_type') == 'interest_only':
            if not data.get('fixed_rate_period_years'):
                raise serializers.ValidationError(
                    'fixed_rate_period_years is required for interest only loans.'
                )
            if not data.get('revert_rate'):
                raise serializers.ValidationError(
                    'revert_rate is required for interest only loans.'
                )

        offset_amount = data.get('offset_amount', Decimal('0'))
        if offset_amount > Decimal('0'):
            if data['rate_type'] != 'variable':
                raise serializers.ValidationError(
                    'Offset accounts can only be attached to variable rate loans.'
                )
            if offset_amount > data['loan_amount']:
                raise serializers.ValidationError(
                    'Offset amount cannot exceed loan amount.'
                )

        return data


class SavedScenarioSerializer(serializers.ModelSerializer):
    splits = LoanSplitSerializer(many=True, read_only=True)

    class Meta:
        model = SavedScenario
        fields = ['id', 'name', 'splits', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        scenario = super().create(validated_data)
        loan_data = self.context.get('loan_data')
        if loan_data:
            result = MortgageCalculatorService.calculate(**loan_data)
            LoanSplit.objects.create(
                scenario=scenario,
                order=1,
                loan_amount=loan_data['loan_amount'],
                annual_rate=loan_data['annual_rate'],
                rate_type=loan_data['rate_type'],
                repayment_type=loan_data['repayment_type'],
                repayment_frequency=loan_data['frequency'],
                loan_term_years=loan_data['loan_term_years'],
                fixed_rate_period_years=loan_data.get('fixed_rate_period_years'),
                revert_rate=loan_data.get('revert_rate'),
                offset_amount=loan_data.get('offset_amount', 0),
                repayment_amount=Decimal(result['repayment_amount']),
                total_interest=Decimal(result['total_interest']),
                total_repayment=Decimal(result['total_repayment']),
            )
        return scenario
