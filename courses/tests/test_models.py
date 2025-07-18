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
            title='Test Course',
            description='Test Description',
            language='English',
            owner=self.user
        )
        
        self.assertEqual(course.title, 'Test Course')
        self.assertEqual(course.owner, self.user)
        self.assertEqual(str(course), 'Test Course')
        
    def test_course_section_creation(self):
        course = Course.objects.create(
            title='Test Course',
            owner=self.user
        )
        
        section = CourseSection.objects.create(
            course=course,
            title='Test Section',
            description='Test Section Description',
            order=1
        )
        
        self.assertEqual(section.course, course)
        self.assertEqual(section.title, 'Test Section')
        self.assertEqual(str(section), 'Test Course - Test Section')