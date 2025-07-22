"""
Health check tests for the courses app.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class CoursesHealthCheckTestCase(APITestCase):
    """Test cases for courses app health check."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        url = reverse('courses_health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('app', response.data)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['app'], 'courses')
        self.assertFalse(response.data['implemented'])
