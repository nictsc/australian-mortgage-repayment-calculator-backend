from abc import ABC, abstractmethod
from decimal import Decimal

"""
This file determines the formula used in the following loan types.
- Principal and Interest (P/I)
- Interest Only (I/O)

UNIT CONTRACT: `annual_rate` here is a decimal FRACTION (0.065 = 6.5%), NOT a percent.
The percent -> fraction conversion (/100) is the caller's responsibility; these classes
never divide by 100. (The live API path in services.py applies /100 itself and does not
call these classes.)
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
