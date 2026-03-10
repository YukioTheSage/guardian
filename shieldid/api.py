import json

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import CourseCertificate, IdentityProfile
from .serializers import (
    CertificateIssueRequestSerializer,
    ConsentRequestSerializer,
    DashboardAddKeySerializer,
    RegisterRequestSerializer,
)
from .utils import generate_passkey_challenge

DASHBOARD_SESSION_KEY = "dashboard_shield_ids"
MAX_DASHBOARD_IDENTITIES = 25


def _add_shield_id_to_dashboard_session(request, shield_id: str) -> None:
    shield_ids = request.session.get(DASHBOARD_SESSION_KEY, [])
    if shield_id in shield_ids:
        shield_ids.remove(shield_id)
    shield_ids.insert(0, shield_id)
    request.session[DASHBOARD_SESSION_KEY] = shield_ids[:MAX_DASHBOARD_IDENTITIES]
    request.session.modified = True


def _dashboard_payload_from_session(request) -> dict:
    shield_ids = request.session.get(DASHBOARD_SESSION_KEY, [])
    if not shield_ids:
        return {
            "keys": [],
            "count": 0,
            "session_bound": True,
        }

    profiles = IdentityProfile.objects.filter(shield_id__in=shield_ids).prefetch_related(
        "certificates"
    )
    profile_map = {profile.shield_id: profile for profile in profiles}

    keys = []
    for shield_id in shield_ids:
        profile = profile_map.get(shield_id)
        if not profile:
            continue

        certificates = list(profile.certificates.all())
        latest_certificate = certificates[0] if certificates else None
        keys.append(
            {
                "shield_id": profile.shield_id,
                "pseudonym": profile.shield_id,
                "verified": profile.verified,
                "age_range": profile.age_range,
                "created_at": profile.created_at.date().isoformat(),
                "certificate_count": len(certificates),
                "latest_certificate_id": (
                    latest_certificate.cert_id if latest_certificate else None
                ),
            }
        )

    return {
        "keys": keys,
        "count": len(keys),
        "session_bound": True,
    }


def _build_passkey_registration_options(identity: IdentityProfile) -> dict:
    rp_id = settings.PASSKEY_RP_ID
    rp_name = settings.PASSKEY_RP_NAME
    try:
        from webauthn import generate_registration_options, options_to_json

        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=rp_name,
            user_id=identity.shield_id.encode("utf-8"),
            user_name=identity.shield_id,
            user_display_name=identity.shield_id,
            challenge=identity.passkey_challenge.encode("utf-8"),
        )
        return json.loads(options_to_json(options))
    except Exception:
        return {
            "challenge": identity.passkey_challenge,
            "rp_id": rp_id,
            "rp_name": rp_name,
            "note": "Fallback challenge payload; full WebAuthn options unavailable.",
        }


@api_view(["POST"])
def register_identity(request):
    serializer = RegisterRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    payload = serializer.validated_data
    profile = IdentityProfile()
    profile.set_sensitive_data(
        name=payload["name"],
        email=payload["email"],
        age=payload["age"],
    )
    profile.save()
    _add_shield_id_to_dashboard_session(request, profile.shield_id)

    demo_certificate = CourseCertificate.objects.create(
        identity=profile,
        course_title="Intro to Privacy Literacy",
        completed=True,
    )

    return Response(
        {
            "shield_id": profile.shield_id,
            "pseudonym": profile.shield_id,
            "verified": profile.verified,
            "age_range": profile.age_range,
            "passkey_challenge": profile.passkey_challenge,
            "passkey_registration_options": _build_passkey_registration_options(profile),
            "demo_certificate_id": demo_certificate.cert_id,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def dashboard_keys(request):
    return Response(_dashboard_payload_from_session(request))


@api_view(["POST"])
def dashboard_add_key(request):
    normalized_payload = request.data.copy()
    shield_id = normalized_payload.get("shield_id")
    if isinstance(shield_id, str):
        normalized_payload["shield_id"] = shield_id.strip().upper()

    serializer = DashboardAddKeySerializer(data=normalized_payload)
    serializer.is_valid(raise_exception=True)

    shield_id = serializer.validated_data["shield_id"]
    get_object_or_404(IdentityProfile, shield_id=shield_id)
    _add_shield_id_to_dashboard_session(request, shield_id)

    return Response(_dashboard_payload_from_session(request), status=status.HTTP_201_CREATED)


@api_view(["POST"])
def dashboard_clear_keys(request):
    request.session[DASHBOARD_SESSION_KEY] = []
    request.session.modified = True
    return Response(_dashboard_payload_from_session(request))


@api_view(["GET"])
def verify_identity(request, shield_id: str):
    profile = get_object_or_404(IdentityProfile, shield_id=shield_id)
    return Response(
        {
            "verified": profile.verified,
            "age_range": profile.age_range,
            "pseudonym": profile.shield_id,
            "created": profile.created_at.date().isoformat(),
        }
    )


@api_view(["POST"])
def consent_release(request, shield_id: str):
    profile = get_object_or_404(IdentityProfile, shield_id=shield_id)
    serializer = ConsentRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    passkey_assertion = serializer.validated_data["passkey_assertion"]
    if passkey_assertion != profile.passkey_challenge:
        return Response(
            {"detail": "Invalid passkey assertion."},
            status=status.HTTP_403_FORBIDDEN,
        )

    requested_fields = serializer.validated_data.get("fields") or ["name", "age"]
    decrypted_payload = profile.decrypted_payload()
    released_payload = {
        field: decrypted_payload[field]
        for field in requested_fields
        if field in decrypted_payload
    }

    if not released_payload:
        return Response(
            {"detail": "No valid fields requested."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile.passkey_challenge = generate_passkey_challenge()
    profile.save(update_fields=["passkey_challenge"])

    return Response(
        {
            "shield_id": profile.shield_id,
            "released": released_payload,
            "next_passkey_challenge": profile.passkey_challenge,
        }
    )


@api_view(["GET"])
def certificate_lookup(request, shield_id: str, cert_id: str):
    certificate = get_object_or_404(
        CourseCertificate.objects.select_related("identity"),
        cert_id=cert_id,
        identity__shield_id=shield_id,
    )
    return Response(
        {
            "pseudonym": certificate.identity.shield_id,
            "course": certificate.course_title,
            "completed": certificate.completed,
            "completed_at": certificate.completed_at.date().isoformat(),
            "cert_id": certificate.cert_id,
        }
    )


@api_view(["POST"])
def issue_certificate(request, shield_id: str):
    profile = get_object_or_404(IdentityProfile, shield_id=shield_id)
    serializer = CertificateIssueRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    certificate = CourseCertificate.objects.create(
        identity=profile,
        course_title=serializer.validated_data["course_title"],
        completed=True,
    )

    return Response(
        {
            "cert_id": certificate.cert_id,
            "pseudonym": profile.shield_id,
            "course": certificate.course_title,
            "completed": certificate.completed,
        },
        status=status.HTTP_201_CREATED,
    )
