from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any

"""
This file describes the business logic behind calculating mortgage repayments.
This determins the following features
- periodic repayments (weekly, fortnightly, monthly)
- loan types (P/I or I/O)
- fixed rates that revert to variable rates
- offset accounts
- rate sensitivity analysis that show the impact of payments to principle and interest when rates changes.
"""

class MortgageCalculatorService:
    PERIODS_PER_YEAR = {
        'weekly': 52,
        'fortnightly': 26,
        'monthly': 12,
    }

    @classmethod
    def calculate(
        cls,
        loan_amount: float,
        annual_rate: float,
        rate_type: str,
        repayment_type: str,
        frequency: str,
        loan_term_years: int,
        fixed_rate_period_years: int = None,
        revert_rate: float = None,
        offset_amount: float = 0,
        rate_change_step: float = 0.25,
    ) -> Dict[str, Any]:
        loan_amount = Decimal(str(loan_amount))
        annual_rate = Decimal(str(annual_rate))
        offset_amount = Decimal(str(offset_amount))
        rate_change_step = Decimal(str(rate_change_step))

        periods_per_year = cls.PERIODS_PER_YEAR[frequency]
        total_periods = loan_term_years * periods_per_year

        if repayment_type == 'interest_only' or (rate_type == 'fixed' and fixed_rate_period_years):
            repayment_amount, schedule, total_interest, total_repayment = cls._calculate_fixed_with_revert(
                loan_amount=loan_amount,
                annual_rate=annual_rate,
                revert_rate=Decimal(str(revert_rate)) if revert_rate else annual_rate,
                rate_type=rate_type,
                repayment_type=repayment_type,
                frequency=frequency,
                loan_term_years=loan_term_years,
                fixed_rate_period_years=fixed_rate_period_years,
                offset_amount=offset_amount,
                periods_per_year=periods_per_year,
            )
        else:
            repayment_amount, schedule, total_interest, total_repayment = cls._calculate_standard(
                loan_amount=loan_amount,
                annual_rate=annual_rate,
                repayment_type=repayment_type,
                frequency=frequency,
                loan_term_years=loan_term_years,
                offset_amount=offset_amount,
                periods_per_year=periods_per_year,
            )

        offset_savings = None
        if offset_amount > 0:
            _, _, total_interest_no_offset, _ = cls._calculate_standard(
                loan_amount=loan_amount,
                annual_rate=annual_rate,
                repayment_type=repayment_type,
                frequency=frequency,
                loan_term_years=loan_term_years,
                offset_amount=Decimal('0'),
                periods_per_year=periods_per_year,
            )
            total_interest_saved = total_interest_no_offset - total_interest
            offset_savings = {
                'repayment_saving_per_period': str(
                    (total_interest_saved / Decimal(total_periods)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                ),
                'total_interest_saved': str(total_interest_saved.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            }

        rate_sensitivity = cls._calculate_rate_sensitivity(
            loan_amount=loan_amount,
            annual_rate=annual_rate,
            rate_type=rate_type,
            repayment_type=repayment_type,
            frequency=frequency,
            loan_term_years=loan_term_years,
            fixed_rate_period_years=fixed_rate_period_years,
            revert_rate=Decimal(str(revert_rate)) if revert_rate else annual_rate,
            offset_amount=offset_amount,
            rate_change_step=rate_change_step,
        )

        return {
            'loan_amount': str(loan_amount),
            'annual_rate': float(annual_rate),
            'rate_type': rate_type,
            'repayment_type': repayment_type,
            'repayment_frequency': frequency,
            'loan_term_years': loan_term_years,
            'fixed_rate_period_years': fixed_rate_period_years,
            'revert_rate': float(revert_rate) if revert_rate else None,
            'offset_amount': str(offset_amount),
            'repayment_amount': str(repayment_amount),
            'total_repayment': str(total_repayment),
            'total_interest': str(total_interest),
            'offset_savings': offset_savings,
            'rate_change_step': float(rate_change_step),
            'rate_sensitivity': rate_sensitivity,
            'schedule': schedule,
        }

    @classmethod
    def _calculate_standard(
        cls,
        loan_amount: Decimal,
        annual_rate: Decimal,
        repayment_type: str,
        frequency: str,
        loan_term_years: int,
        offset_amount: Decimal,
        periods_per_year: int,
    ):
        effective_loan = loan_amount - offset_amount
        total_periods = loan_term_years * periods_per_year
        # Unit boundary: annual_rate arrives as a PERCENT (e.g. 6.0). The /100 to a
        # decimal fraction happens here in the service layer only -- never in the views,
        # serializers, or the calculators.py strategy classes.
        periodic_rate = (annual_rate / Decimal('100')) / Decimal(periods_per_year)

        if repayment_type == 'interest_only':
            repayment_amount = effective_loan * periodic_rate
        else:
            if periodic_rate == 0:
                repayment_amount = effective_loan / Decimal(total_periods)
            else:
                repayment_amount = effective_loan * periodic_rate * ((Decimal('1') + periodic_rate) ** total_periods) / (
                    ((Decimal('1') + periodic_rate) ** total_periods) - Decimal('1')
                )

        # Round the quoted repayment to cents first, then amortise from that figure and
        # derive the totals by summing the schedule rows, so every dollar amount ties out
        # to the schedule (matching the fixed-rate path's approach).
        repayment_amount = repayment_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        schedule, closing_balance = cls._build_schedule(
            effective_loan=effective_loan,
            repayment_amount=repayment_amount,
            periodic_rate=periodic_rate,
            total_periods=total_periods,
            phase='fixed' if repayment_type == 'interest_only' else None,
        )

        total_interest = sum(Decimal(row['interest']) for row in schedule)
        total_repayment = sum(Decimal(row['principal']) for row in schedule) + total_interest

        return repayment_amount, schedule, total_interest, total_repayment

    @classmethod
    def _calculate_fixed_with_revert(
        cls,
        loan_amount: Decimal,
        annual_rate: Decimal,
        revert_rate: Decimal,
        rate_type: str,
        repayment_type: str,
        frequency: str,
        loan_term_years: int,
        fixed_rate_period_years: int,
        offset_amount: Decimal,
        periods_per_year: int,
    ):
        effective_loan = loan_amount - offset_amount if rate_type == 'variable' else loan_amount
        fixed_periods = fixed_rate_period_years * periods_per_year
        remaining_years = loan_term_years - fixed_rate_period_years
        remaining_periods = remaining_years * periods_per_year
        total_periods = loan_term_years * periods_per_year

        fixed_periodic_rate = (annual_rate / Decimal('100')) / Decimal(periods_per_year)
        revert_periodic_rate = (revert_rate / Decimal('100')) / Decimal(periods_per_year)

        if repayment_type == 'interest_only':
            fixed_repayment = loan_amount * fixed_periodic_rate
            revert_periodic_rate_for_calc = revert_periodic_rate
            if revert_periodic_rate_for_calc == 0:
                revert_repayment = loan_amount / Decimal(remaining_periods)
            else:
                revert_repayment = loan_amount * revert_periodic_rate_for_calc * ((Decimal('1') + revert_periodic_rate_for_calc) ** remaining_periods) / (
                    ((Decimal('1') + revert_periodic_rate_for_calc) ** remaining_periods) - Decimal('1')
                )
        else:
            if fixed_periodic_rate == 0:
                fixed_repayment = loan_amount / Decimal(total_periods)
            else:
                fixed_repayment = loan_amount * fixed_periodic_rate * ((Decimal('1') + fixed_periodic_rate) ** total_periods) / (
                    ((Decimal('1') + fixed_periodic_rate) ** total_periods) - Decimal('1')
                )

            if revert_periodic_rate == 0:
                revert_repayment = loan_amount / Decimal(remaining_periods)
            else:
                revert_repayment = loan_amount * revert_periodic_rate * ((Decimal('1') + revert_periodic_rate) ** remaining_periods) / (
                    ((Decimal('1') + revert_periodic_rate) ** remaining_periods) - Decimal('1')
                )

        # Round both quoted repayments to cents before amortising, so the schedule rows
        # (and the totals summed from them) tie out to the displayed repayment.
        fixed_repayment = fixed_repayment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        revert_repayment = revert_repayment.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        schedule = []
        closing_balance = loan_amount if repayment_type == 'interest_only' else effective_loan

        for period in range(1, fixed_periods + 1):
            interest = closing_balance * fixed_periodic_rate
            principal = fixed_repayment - interest

            if repayment_type == 'interest_only':
                principal = Decimal('0')
                closing_balance = loan_amount
            else:
                closing_balance = closing_balance - principal

            schedule.append({
                'period': period,
                'phase': 'interest_only' if repayment_type == 'interest_only' else 'fixed',
                'principal': str(principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'interest': str(interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'closing_balance': str(closing_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            })

        for period in range(fixed_periods + 1, total_periods + 1):
            interest = closing_balance * revert_periodic_rate
            principal = revert_repayment - interest
            closing_balance = closing_balance - principal

            schedule.append({
                'period': period,
                'phase': 'variable',
                'principal': str(principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'interest': str(interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'closing_balance': str(closing_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            })

        if schedule and schedule[-1]['closing_balance'] != '0.00':
            last_period = schedule[-1]
            diff = Decimal(last_period['closing_balance'])
            last_period['principal'] = str((Decimal(last_period['principal']) - diff).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            last_period['closing_balance'] = '0.00'

        total_principal = sum(Decimal(row['principal']) for row in schedule)
        total_interest = sum(Decimal(row['interest']) for row in schedule)
        total_repayment = total_principal + total_interest

        first_repayment = fixed_repayment

        return first_repayment, schedule, total_interest, total_repayment

    @classmethod
    def _build_schedule(cls, effective_loan, repayment_amount, periodic_rate, total_periods, phase=None):
        schedule = []
        closing_balance = effective_loan

        for period in range(1, int(total_periods) + 1):
            interest = closing_balance * periodic_rate
            principal = repayment_amount - interest
            closing_balance = closing_balance - principal

            schedule.append({
                'period': period,
                'phase': phase,
                'principal': str(principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'interest': str(interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'closing_balance': str(closing_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            })

        if schedule and schedule[-1]['closing_balance'] != '0.00':
            last_period = schedule[-1]
            diff = Decimal(last_period['closing_balance'])
            last_period['principal'] = str((Decimal(last_period['principal']) - diff).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            last_period['closing_balance'] = '0.00'

        return schedule, closing_balance

    @classmethod
    def _calculate_rate_sensitivity(
        cls,
        loan_amount: Decimal,
        annual_rate: Decimal,
        rate_type: str,
        repayment_type: str,
        frequency: str,
        loan_term_years: int,
        fixed_rate_period_years: int,
        revert_rate: Decimal,
        offset_amount: Decimal,
        rate_change_step: Decimal,
    ):
        if rate_type == 'fixed' or repayment_type == 'interest_only':
            minus_rate = revert_rate - rate_change_step
            plus_rate = revert_rate + rate_change_step
            adjusted_revert_minus = minus_rate
            adjusted_revert_plus = plus_rate
            adjusted_annual_minus = annual_rate
            adjusted_annual_plus = annual_rate
        else:
            minus_rate = annual_rate - rate_change_step
            plus_rate = annual_rate + rate_change_step
            adjusted_revert_minus = revert_rate
            adjusted_revert_plus = revert_rate
            adjusted_annual_minus = minus_rate
            adjusted_annual_plus = plus_rate

        minus_repayment, _, minus_interest, minus_total_repayment = cls._get_calculation_results(
            loan_amount=loan_amount,
            annual_rate=adjusted_annual_minus,
            rate_type=rate_type,
            repayment_type=repayment_type,
            frequency=frequency,
            loan_term_years=loan_term_years,
            fixed_rate_period_years=fixed_rate_period_years,
            revert_rate=adjusted_revert_minus,
            offset_amount=offset_amount,
        )

        plus_repayment, _, plus_interest, plus_total_repayment = cls._get_calculation_results(
            loan_amount=loan_amount,
            annual_rate=adjusted_annual_plus,
            rate_type=rate_type,
            repayment_type=repayment_type,
            frequency=frequency,
            loan_term_years=loan_term_years,
            fixed_rate_period_years=fixed_rate_period_years,
            revert_rate=adjusted_revert_plus,
            offset_amount=offset_amount,
        )

        return {
            'step': float(rate_change_step),
            'minus': {
                # The rate actually varied: revert_rate for fixed/IO loans, annual_rate for variable.
                'rate_used': float(minus_rate),
                'repayment_amount': str(minus_repayment),
                'total_interest': str(minus_interest),
                'total_repayment': str(minus_total_repayment),
            },
            'plus': {
                # The rate actually varied: revert_rate for fixed/IO loans, annual_rate for variable.
                'rate_used': float(plus_rate),
                'repayment_amount': str(plus_repayment),
                'total_interest': str(plus_interest),
                'total_repayment': str(plus_total_repayment),
            },
        }

    @classmethod
    def _get_calculation_results(
        cls,
        loan_amount: Decimal,
        annual_rate: Decimal,
        rate_type: str,
        repayment_type: str,
        frequency: str,
        loan_term_years: int,
        fixed_rate_period_years: int,
        revert_rate: Decimal,
        offset_amount: Decimal,
    ):
        periods_per_year = cls.PERIODS_PER_YEAR[frequency]

        if repayment_type == 'interest_only' or (rate_type == 'fixed' and fixed_rate_period_years):
            repayment_amount, _, total_interest, total_repayment = cls._calculate_fixed_with_revert(
                loan_amount=loan_amount,
                annual_rate=annual_rate,
                revert_rate=revert_rate,
                rate_type=rate_type,
                repayment_type=repayment_type,
                frequency=frequency,
                loan_term_years=loan_term_years,
                fixed_rate_period_years=fixed_rate_period_years,
                offset_amount=offset_amount,
                periods_per_year=periods_per_year,
            )
        else:
            repayment_amount, _, total_interest, total_repayment = cls._calculate_standard(
                loan_amount=loan_amount,
                annual_rate=annual_rate,
                repayment_type=repayment_type,
                frequency=frequency,
                loan_term_years=loan_term_years,
                offset_amount=offset_amount,
                periods_per_year=periods_per_year,
            )

        return repayment_amount, None, total_interest, total_repayment
