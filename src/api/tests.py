from django.test import TestCase
from django.urls import reverse


# Create your tests here.
class TestHealthCheck(TestCase):
    def test_health_check(self):
        url = reverse("health-check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
