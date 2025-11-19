from django.contrib import admin
from django.contrib.admin import register

from main.models import Organization


# Register your models here.
@register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "contact_number", "email", "is_active", 'created_at')
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("created_at",)

