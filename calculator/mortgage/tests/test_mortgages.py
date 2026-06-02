import pytest
from decimal import Decimal
from mortgage.calculators import PrincipalAndInterest, InterestOnly

class TestPrincipalAndInterest:
    ## Test suite for principle and interest calculations

    def test_calculate_repayment_basic(self):
        ## Test basic repayment calculation
        calculator = PrincipalAndInterest()

        ## Arrange
        loan_amount = Decimal('300000')
        annual_rate = Decimal('0.065') ## 6.5%
        periods = 360 ## 30 years * 12 months

        ## Act
        result = calculator.calculate_repayment(loan_amount, annual_rate, periods)

        ## Assert
        assert result > 0
        assert result == pytest.approx(Decimal('1896.20'), abs=Decimal('1'))

class TestInterestOnly:
    ## Test suite for interest only calculations

    def test_calculate_repayment(self):
        ## Test interest only repayment calculation
        calculator = InterestOnly

        ## Arrange
        loan_amount = Decimal('300000')
        annual_rate = Decimal('0.065')
        periods = 12 ## Monthly repayments per year

        result = calculator.calculate_repayment(loan_amount, annual_rate, periods)

        ## Interest incurred = loan * (rate / periods)
        expected = Decimal('300000') * (Decimal('0.065') / Decimal('12'))
        assert result == pytest.approx(expected, abs=Decimal('0.01'))
