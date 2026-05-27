# Django admin configuration for the mortgage app
# Enables staff users to view, search, and filter saved mortgage scenarios in the admin panel

from django.contrib import admin

from .models import SavedScenario


@admin.register(SavedScenario)
class SavedScenarioAdmin(admin.ModelAdmin):
    # Display key mortgage parameters and metadata in the list view
    list_display = ['name', 'user', 'loan_amount', 'annual_rate', 'rate_type', 'repayment_type', 'repayment_frequency', 'created_at']
    # Allow filtering by scenario characteristics
    list_filter = ['rate_type', 'repayment_type', 'repayment_frequency']
    # Allow searching by scenario name or user identifiers
    search_fields = ['name', 'user__auth0_id', 'user__email']
    # Calculated and timestamp fields are read-only; user cannot edit them directly
    readonly_fields = ['repayment_amount', 'total_interest', 'total_repayment', 'created_at', 'updated_at']
