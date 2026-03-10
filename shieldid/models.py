from django.db import models
from django.utils import timezone

from .utils import (
    age_to_range,
    decrypt_value,
    encrypt_value,
    generate_certificate_id,
    generate_passkey_challenge,
    generate_shield_id,
)


class IdentityProfile(models.Model):
    shield_id = models.CharField(max_length=11, unique=True, db_index=True)
    encrypted_name = models.TextField()
    encrypted_email = models.TextField()
    encrypted_age = models.TextField()
    age_range = models.CharField(max_length=32)
    verified = models.BooleanField(default=True)
    passkey_challenge = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.shield_id

    def set_sensitive_data(self, *, name: str, email: str, age: int) -> None:
        self.encrypted_name = encrypt_value(name)
        self.encrypted_email = encrypt_value(email)
        self.encrypted_age = encrypt_value(str(age))
        self.age_range = age_to_range(age)

    def decrypted_payload(self) -> dict[str, str | int]:
        return {
            "name": decrypt_value(self.encrypted_name),
            "email": decrypt_value(self.encrypted_email),
            "age": int(decrypt_value(self.encrypted_age)),
            "age_range": self.age_range,
            "shield_id": self.shield_id,
        }

    def save(self, *args, **kwargs):
        if not self.shield_id:
            for _ in range(20):
                candidate = generate_shield_id()
                if not IdentityProfile.objects.filter(shield_id=candidate).exists():
                    self.shield_id = candidate
                    break
            else:
                raise RuntimeError("Unable to generate a unique shield_id")

        if not self.passkey_challenge:
            self.passkey_challenge = generate_passkey_challenge()

        super().save(*args, **kwargs)


class CourseCertificate(models.Model):
    identity = models.ForeignKey(
        IdentityProfile,
        related_name="certificates",
        on_delete=models.CASCADE,
    )
    cert_id = models.CharField(max_length=13, unique=True, db_index=True)
    course_title = models.CharField(max_length=200)
    completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.cert_id} ({self.identity.shield_id})"

    def save(self, *args, **kwargs):
        if not self.cert_id:
            for _ in range(20):
                candidate = generate_certificate_id()
                if not CourseCertificate.objects.filter(cert_id=candidate).exists():
                    self.cert_id = candidate
                    break
            else:
                raise RuntimeError("Unable to generate a unique cert_id")

        super().save(*args, **kwargs)
