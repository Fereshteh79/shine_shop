from django.test import TestCase


class SecurityTests(TestCase):
    def test_security_headers_in_debug_mode(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Strict-Transport-Security", response.headers)
