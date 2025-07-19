from django.test import TestCase
from django.contrib.auth import get_user_model
from courses.models import Course, CourseSection, Document, DocumentTag

User = get_user_model()


class CourseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_course_creation(self):
        course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            language='en',
            user=self.user
        )
        
        self.assertEqual(course.name, 'Test Course')
        self.assertEqual(course.user, self.user)
        self.assertEqual(str(course), 'Test Course (testuser)')
        
    def test_course_section_creation(self):
        course = Course.objects.create(
            name='Test Course',
            user=self.user
        )
        
        section = CourseSection.objects.create(
            course=course,
            name='Test Section',
            description='Test Section Description',
            order=1
        )
        
        self.assertEqual(section.course, course)
        self.assertEqual(section.name, 'Test Section')
        self.assertEqual(str(section), 'Test Course - Test Section')