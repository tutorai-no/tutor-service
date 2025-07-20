from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse


# Create your tests here.
class TestHealthCheck(TestCase):
    def test_health_check(self):
        url = reverse("health-check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch("learning_materials.knowledge_base.db_interface.MockDatabase.is_reachable")
    def test_health_check_database_down(self, mock_is_reachable):
        mock_is_reachable.return_value = False
        url = reverse("health-check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content, b'"RAG Database is unreachable"')
