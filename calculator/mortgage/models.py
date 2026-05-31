from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from decimal import Decimal


class SavedScenario(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_scenarios',
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user})'


class LoanSplit(models.Model):
    RATE_TYPE_CHOICES = [
        ('variable', 'Variable'),
        ('fixed', 'Fixed'),
    ]
    REPAYMENT_TYPE_CHOICES = [
        ('principal_and_interest', 'Principal & Interest'),
        ('interest_only', 'Interest Only'),
    ]
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('fortnightly', 'Fortnightly'),
        ('monthly', 'Monthly'),
    ]

    scenario = models.ForeignKey(
        SavedScenario,
        on_delete=models.CASCADE,
        related_name='splits',
    )
    order = models.PositiveSmallIntegerField(default=1)

    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    annual_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('20.00'))]
    )
    rate_type = models.CharField(max_length=10, choices=RATE_TYPE_CHOICES)
    repayment_type = models.CharField(max_length=25, choices=REPAYMENT_TYPE_CHOICES)
    repayment_frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES)
    loan_term_years = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(40)]
    )
    fixed_rate_period_years = models.PositiveSmallIntegerField(null=True, blank=True)
    revert_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('20.00'))]
    )
    offset_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text='Offset account for variable rate loans only',
    )

    repayment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_interest = models.DecimalField(max_digits=15, decimal_places=2)
    total_repayment = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        ordering = ['order']
        unique_together = [('scenario', 'order')]

    def __str__(self):
        return f'{self.scenario.name} - Split {self.order}'
