from django.urls import path

from . import api, views

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path("register/", views.registration_page, name="registration-page"),
    path("dashboard/", views.dashboard_page, name="dashboard-page"),
    path("verify/", views.verification_page, name="verification-page"),
    path("edtech-demo/", views.edtech_demo_page, name="edtech-demo-page"),
    path("api/register/", api.register_identity, name="register-identity"),
    path("api/me/keys/", api.dashboard_keys, name="dashboard-keys"),
    path("api/me/keys/add/", api.dashboard_add_key, name="dashboard-add-key"),
    path("api/me/keys/clear/", api.dashboard_clear_keys, name="dashboard-clear-keys"),
    path("api/verify/<str:shield_id>/", api.verify_identity, name="verify-identity"),
    path("api/consent/<str:shield_id>/", api.consent_release, name="consent-release"),
    path(
        "api/certificate/<str:shield_id>/issue/",
        api.issue_certificate,
        name="issue-certificate",
    ),
    path(
        "api/certificate/<str:shield_id>/<str:cert_id>/",
        api.certificate_lookup,
        name="certificate-lookup",
    ),
]
