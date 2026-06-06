"""Invariants for MortgageCalculatorService money output.

Locks in two guarantees that are easy to regress:
  1. Every dollar field in the response is a string with exactly 2 decimal places.
  2. The totals tie out to the amortization schedule (round-then-derive), and the
     schedule clears to 0.00.
"""
from decimal import Decimal

import pytest

from mortgage.services import MortgageCalculatorService as Service


# (name, kwargs) covering every code path: variable/fixed, P&I/interest-only,
# each frequency, with and without an offset.
SCENARIOS = [
    ('variable P&I monthly', dict(
        loan_amount=650000, annual_rate=6.20, rate_type='variable',
        repayment_type='principal_and_interest', frequency='monthly', loan_term_years=30)),
    ('variable P&I fortnightly + offset', dict(
        loan_amount=650000, annual_rate=6.20, rate_type='variable',
        repayment_type='principal_and_interest', frequency='fortnightly', loan_term_years=30,
        offset_amount=50000)),
    ('variable P&I weekly', dict(
        loan_amount=350000, annual_rate=5.50, rate_type='variable',
        repayment_type='principal_and_interest', frequency='weekly', loan_term_years=25)),
    ('fixed 3yr P&I monthly', dict(
        loan_amount=500000, annual_rate=5.89, rate_type='fixed',
        repayment_type='principal_and_interest', frequency='monthly', loan_term_years=30,
        fixed_rate_period_years=3, revert_rate=6.50)),
    ('interest_only 5yr monthly', dict(
        loan_amount=500000, annual_rate=6.10, rate_type='variable',
        repayment_type='interest_only', frequency='monthly', loan_term_years=30,
        fixed_rate_period_years=5, revert_rate=6.10)),
    ('interest_only fortnightly + offset', dict(
        loan_amount=600000, annual_rate=5.95, rate_type='variable',
        repayment_type='interest_only', frequency='fortnightly', loan_term_years=30,
        fixed_rate_period_years=5, revert_rate=6.40, offset_amount=40000)),
]

IDS = [name for name, _ in SCENARIOS]


def has_two_decimals(value):
    """True if `value` is a string money amount with exactly 2 decimal places."""
    return isinstance(value, str) and '.' in value and len(value.split('.')[1]) == 2


def money_fields(result):
    """Yield (label, value) for every dollar amount in a calculate() result."""
    yield 'repayment_amount', result['repayment_amount']
    yield 'total_repayment', result['total_repayment']
    yield 'total_interest', result['total_interest']

    for side in ('minus', 'plus'):
        bucket = result['rate_sensitivity'][side]
        yield f'sensitivity.{side}.repayment_amount', bucket['repayment_amount']
        yield f'sensitivity.{side}.total_interest', bucket['total_interest']
        yield f'sensitivity.{side}.total_repayment', bucket['total_repayment']

    if result.get('offset_savings'):
        yield 'offset.repayment_saving_per_period', result['offset_savings']['repayment_saving_per_period']
        yield 'offset.total_interest_saved', result['offset_savings']['total_interest_saved']

    for row in result['schedule']:
        yield 'schedule.principal', row['principal']
        yield 'schedule.interest', row['interest']
        yield 'schedule.closing_balance', row['closing_balance']


@pytest.mark.parametrize('name, kwargs', SCENARIOS, ids=IDS)
class TestMoneyRounding:
    def test_all_dollar_fields_have_two_decimals(self, name, kwargs):
        result = Service.calculate(**kwargs)
        offenders = {label: value for label, value in money_fields(result) if not has_two_decimals(value)}
        assert not offenders, f'fields without exactly 2 decimals: {offenders}'

    def test_totals_tie_out_to_schedule(self, name, kwargs):
        result = Service.calculate(**kwargs)
        schedule = result['schedule']

        sum_principal = sum(Decimal(row['principal']) for row in schedule)
        sum_interest = sum(Decimal(row['interest']) for row in schedule)

        assert Decimal(result['total_interest']) == sum_interest
        assert Decimal(result['total_repayment']) == sum_principal + sum_interest

    def test_schedule_clears_to_zero(self, name, kwargs):
        result = Service.calculate(**kwargs)
        assert result['schedule'][-1]['closing_balance'] == '0.00'
