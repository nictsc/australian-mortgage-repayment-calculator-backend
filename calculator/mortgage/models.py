from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models


class SavedScenario(models.Model):
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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_scenarios',
    )
    name = models.CharField(max_length=255)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    annual_rate = models.DecimalField(max_digits=4, decimal_places=2)
    rate_type = models.CharField(max_length=10, choices=RATE_TYPE_CHOICES)
    repayment_type = models.CharField(max_length=25, choices=REPAYMENT_TYPE_CHOICES)
    repayment_frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES)
    loan_term_years = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(40)]
    )
    offset_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Offset account for variable rate loans only',
    )

    # Computed and stored at save time
    repayment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_interest = models.DecimalField(max_digits=15, decimal_places=2)
    total_repayment = models.DecimalField(max_digits=15, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user})'
