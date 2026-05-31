from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

"""
This file describes the User Admin dashboard to manage user accounts. 
"""
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Auth0', {'fields': ('auth0_id',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'auth0_id')
