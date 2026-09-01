from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'address', 'village_or_city', 'state', 'is_verified_farmer')}),
    )
    list_display = ['username', 'email', 'role', 'is_verified_farmer']
    list_filter = ['role', 'is_verified_farmer']

admin.site.register(User, CustomUserAdmin)
