from django.contrib import admin
from .models import Appointment, PatientFeedback


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "token_number",
        "patient_name",
        "doctor",
        "appointment_date",
        "appointment_time",
        "status",
        "priority",
        "risk_score",
        "mobile_number",
        "created_at",
    )
    list_filter = ("status", "priority", "doctor", "appointment_date")
    search_fields = ("patient_name", "mobile_number", "doctor", "symptoms")
    ordering = ("-appointment_date", "token_number", "-id")
    readonly_fields = ("created_at",)
    list_editable = ("status",)


@admin.register(PatientFeedback)
class PatientFeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "short_message", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "email", "message")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    def short_message(self, obj):
        if len(obj.message) > 60:
            return obj.message[:57] + "..."
        return obj.message

    short_message.short_description = "Message Preview"
