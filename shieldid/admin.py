from django.contrib import admin

from .models import CourseCertificate, IdentityProfile


@admin.register(IdentityProfile)
class IdentityProfileAdmin(admin.ModelAdmin):
    list_display = ("shield_id", "age_range", "verified", "created_at")
    search_fields = ("shield_id", "age_range")
    readonly_fields = (
        "shield_id",
        "encrypted_name",
        "encrypted_email",
        "encrypted_age",
        "age_range",
        "passkey_challenge",
        "created_at",
    )


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    list_display = ("cert_id", "identity", "course_title", "completed", "completed_at")
    search_fields = ("cert_id", "identity__shield_id", "course_title")
