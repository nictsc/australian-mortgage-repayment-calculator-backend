from decimal import Decimal
from rest_framework import serializers

from .models import SavedScenario
from .services import MortgageCalculatorService


class CalculatorInputSerializer(serializers.Serializer):
    loan_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('1.00')
    )
    annual_rate = serializers.DecimalField(
        max_digits=4, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('99.99')
    )
    rate_type = serializers.ChoiceField(choices=['variable', 'fixed'])
    repayment_type = serializers.ChoiceField(choices=['principal_and_interest', 'interest_only'])
    repayment_frequency = serializers.ChoiceField(choices=['weekly', 'fortnightly', 'monthly'])
    loan_term_years = serializers.IntegerField(min_value=1, max_value=40)
    offset_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('0.00'), default=Decimal('0.00')
    )

    def validate(self, data):
        if data['rate_type'] == 'fixed' and data['loan_term_years'] > 5:
            raise serializers.ValidationError(
                'Fixed rate loans are limited to a maximum of 5 years.'
            )
        if data['repayment_type'] == 'interest_only' and data['loan_term_years'] > 5:
            raise serializers.ValidationError(
                'Interest only loans are limited to a maximum of 5 years.'
            )

        # Offset validation
        if data.get('offset_amount', Decimal('0')) > Decimal('0'):
            if data['rate_type'] != 'variable':
                raise serializers.ValidationError(
                    'Offset accounts can only be attached to variable rate loans.'
                )
            if data['offset_amount'] > data['loan_amount']:
                raise serializers.ValidationError(
                    'Offset amount cannot exceed loan amount.'
                )

        return data


class CalculatorResultSerializer(serializers.Serializer):
    repayment_amount = serializers.CharField()
    total_repayment = serializers.CharField()
    total_interest = serializers.CharField()
    frequency = serializers.CharField()
    repayment_type = serializers.CharField()
    loan_amount = serializers.CharField()
    annual_rate = serializers.FloatField()
    loan_term_years = serializers.IntegerField()
    offset_amount = serializers.CharField()


class SavedScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedScenario
        fields = [
            'id', 'name',
            'loan_amount', 'annual_rate', 'rate_type',
            'repayment_type', 'repayment_frequency', 'loan_term_years',
            'offset_amount', 'repayment_amount', 'total_interest', 'total_repayment',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'repayment_amount', 'total_interest', 'total_repayment', 'created_at', 'updated_at']

    def validate_loan_term_years(self, value):
        if value > 40:
            raise serializers.ValidationError('Loan term cannot exceed 40 years.')
        return value

    def validate(self, data):
        if data.get('rate_type') == 'fixed' and data.get('loan_term_years', 0) > 5:
            raise serializers.ValidationError(
                'Fixed rate loans are limited to a maximum of 5 years.'
            )
        if data.get('repayment_type') == 'interest_only' and data.get('loan_term_years', 0) > 5:
            raise serializers.ValidationError(
                'Interest only loans are limited to a maximum of 5 years.'
            )

        # Offset validation
        offset = data.get('offset_amount', Decimal('0'))
        if offset > Decimal('0'):
            if data.get('rate_type') != 'variable':
                raise serializers.ValidationError(
                    'Offset accounts can only be attached to variable rate loans.'
                )
            if offset > data.get('loan_amount', 0):
                raise serializers.ValidationError(
                    'Offset amount cannot exceed loan amount.'
                )

        return data

    def create(self, validated_data):
        result = MortgageCalculatorService.calculate(
            loan_amount=float(validated_data['loan_amount']),
            annual_rate=float(validated_data['annual_rate']),
            repayment_type=validated_data['repayment_type'],
            frequency=validated_data['repayment_frequency'],
            loan_term_years=validated_data['loan_term_years'],
            offset_amount=float(validated_data.get('offset_amount', 0)),
        )
        validated_data['repayment_amount'] = result['repayment_amount']
        validated_data['total_interest'] = result['total_interest']
        validated_data['total_repayment'] = result['total_repayment']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        result = MortgageCalculatorService.calculate(
            loan_amount=float(validated_data.get('loan_amount', instance.loan_amount)),
            annual_rate=float(validated_data.get('annual_rate', instance.annual_rate)),
            repayment_type=validated_data.get('repayment_type', instance.repayment_type),
            frequency=validated_data.get('repayment_frequency', instance.repayment_frequency),
            loan_term_years=validated_data.get('loan_term_years', instance.loan_term_years),
            offset_amount=float(validated_data.get('offset_amount', instance.offset_amount)),
        )
        validated_data['repayment_amount'] = result['repayment_amount']
        validated_data['total_interest'] = result['total_interest']
        validated_data['total_repayment'] = result['total_repayment']
        return super().update(instance, validated_data)
