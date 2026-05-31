from django.contrib import admin

from .models import SavedScenario, LoanSplit

"""
This file sets up the Django Admin dashboard which controls the following features.
- Saved Scenario Admin to let admins view saved mortgage scenarios.
- Loan Split Admin to let admins view and manage loan splits within scenarios.
- Loan Split Inline as a special view to show loans directly in the scenario.
"""

class LoanSplitInline(admin.TabularInline):
    model = LoanSplit
    extra = 0
    readonly_fields = ['repayment_amount', 'total_interest', 'total_repayment']
    fields = [
        'order', 'loan_amount', 'annual_rate', 'rate_type',
        'repayment_type', 'repayment_frequency', 'loan_term_years',
        'fixed_rate_period_years', 'revert_rate', 'offset_amount',
        'repayment_amount', 'total_interest', 'total_repayment'
    ]


@admin.register(SavedScenario)
class SavedScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__auth0_id', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [LoanSplitInline]


@admin.register(LoanSplit)
class LoanSplitAdmin(admin.ModelAdmin):
    list_display = ['scenario', 'order', 'loan_amount', 'annual_rate', 'rate_type', 'repayment_type']
    list_filter = ['rate_type', 'repayment_type', 'repayment_frequency']
    search_fields = ['scenario__name', 'scenario__user__email']
    readonly_fields = ['repayment_amount', 'total_interest', 'total_repayment']
