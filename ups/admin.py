from django.contrib import admin

from .models import ServiceRequest


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):

    list_display = (
        "client_id",
        "customer_name",
        "mobile_number",
        "engineer",
        "created_at",
    )

    search_fields = (
        "client_id",
        "customer_name",
        "mobile_number",
    )

    list_filter = (
        "created_at",
        "engineer",
    )