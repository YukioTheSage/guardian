import json

from django.test import TestCase
from django.urls import reverse

from .api import DASHBOARD_SESSION_KEY
from .models import CourseCertificate, IdentityProfile


class DashboardSessionFlowTests(TestCase):
    def test_register_identity_auto_adds_key_to_dashboard(self):
        response = self.client.post(
            reverse("register-identity"),
            data=json.dumps(
                {
                    "name": "Alex",
                    "age": 14,
                    "email": "alex@example.com",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()

        session = self.client.session
        self.assertIn(payload["shield_id"], session.get(DASHBOARD_SESSION_KEY, []))

        dashboard_response = self.client.get(reverse("dashboard-keys"))
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard_payload = dashboard_response.json()
        self.assertEqual(dashboard_payload["count"], 1)
        self.assertEqual(dashboard_payload["keys"][0]["shield_id"], payload["shield_id"])

    def test_dashboard_add_key_adds_existing_identity(self):
        profile = IdentityProfile()
        profile.set_sensitive_data(
            name="Jamie",
            email="jamie@example.com",
            age=16,
        )
        profile.save()

        add_response = self.client.post(
            reverse("dashboard-add-key"),
            data=json.dumps({"shield_id": profile.shield_id}),
            content_type="application/json",
        )
        self.assertEqual(add_response.status_code, 201)
        payload = add_response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["keys"][0]["shield_id"], profile.shield_id)

        duplicate_response = self.client.post(
            reverse("dashboard-add-key"),
            data=json.dumps({"shield_id": profile.shield_id}),
            content_type="application/json",
        )
        self.assertEqual(duplicate_response.status_code, 201)
        duplicate_payload = duplicate_response.json()
        self.assertEqual(duplicate_payload["count"], 1)

    def test_dashboard_clear_keys_empties_session_collection(self):
        response = self.client.post(
            reverse("register-identity"),
            data=json.dumps(
                {
                    "name": "Mina",
                    "age": 15,
                    "email": "mina@example.com",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        clear_response = self.client.post(reverse("dashboard-clear-keys"))
        self.assertEqual(clear_response.status_code, 200)
        payload = clear_response.json()
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["keys"], [])


class CertificateEndpointRoutingTests(TestCase):
    def setUp(self):
        self.profile = IdentityProfile()
        self.profile.set_sensitive_data(
            name="Robin",
            email="robin@example.com",
            age=17,
        )
        self.profile.save()

    def test_issue_certificate_route_accepts_post(self):
        response = self.client.post(
            reverse("issue-certificate", args=[self.profile.shield_id]),
            data=json.dumps({"course_title": "Privacy 101"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["pseudonym"], self.profile.shield_id)
        self.assertEqual(payload["course"], "Privacy 101")
        self.assertTrue(payload["completed"])
        self.assertTrue(
            CourseCertificate.objects.filter(
                cert_id=payload["cert_id"],
                identity=self.profile,
                course_title="Privacy 101",
            ).exists()
        )
