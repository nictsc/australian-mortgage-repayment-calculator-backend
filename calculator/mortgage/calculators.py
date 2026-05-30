from abc import ABC, abstractmethod
from decimal import Decimal

"""
This file determines the formula used in the following loan types.
- Principal and Interest (P/I)
- Interest Only (I/O)
"""
class MortgageCalculator(ABC):
    @abstractmethod
    def calculate_repayment(
        self,
        loan_amount: Decimal,
        annual_rate: Decimal,
        periods: int,
    ) -> Decimal:
        pass


class PrincipalAndInterest(MortgageCalculator):
    def calculate_repayment(
        self,
        loan_amount: Decimal,
        annual_rate: Decimal,
        periods: int,
    ) -> Decimal:
        periodic_rate = annual_rate / Decimal(periods)
        if periodic_rate == 0:
            return loan_amount / Decimal(periods)
        return loan_amount * periodic_rate * ((Decimal('1') + periodic_rate) ** periods) / (
            ((Decimal('1') + periodic_rate) ** periods) - Decimal('1')
        )


class InterestOnly(MortgageCalculator):
    def calculate_repayment(
        self,
        loan_amount: Decimal,
        annual_rate: Decimal,
        periods: int,
    ) -> Decimal:
        periodic_rate = annual_rate / Decimal(periods)
        return loan_amount * periodic_rate
