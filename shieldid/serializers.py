from rest_framework import serializers


class RegisterRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, trim_whitespace=True)
    age = serializers.IntegerField(min_value=5, max_value=120)
    email = serializers.EmailField(max_length=254)


class ConsentRequestSerializer(serializers.Serializer):
    passkey_assertion = serializers.CharField(max_length=255, trim_whitespace=True)
    fields = serializers.ListField(
        child=serializers.ChoiceField(choices=["name", "email", "age", "age_range"]),
        required=False,
        allow_empty=True,
    )


class CertificateIssueRequestSerializer(serializers.Serializer):
    course_title = serializers.CharField(max_length=200)


class DashboardAddKeySerializer(serializers.Serializer):
    shield_id = serializers.RegexField(
        regex=r"^SH-[A-Z0-9]{4}-[A-Z0-9]{4}$",
        max_length=12,
        min_length=12,
    )
