from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Course, Lecture, HomeworkAssignment, HomeworkSubmission, Grade, GradeComment
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class UserAuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
    def test_student_registration(self):
        url = reverse('register')
        data = {
            'username': 'teststudent',
            'email': 'student@test.com',
            'first_name': 'Test',
            'last_name': 'Student',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'student'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().role, 'student')
        
    def test_teacher_registration(self):
        url = reverse('register')
        data = {
            'username': 'testteacher',
            'email': 'teacher@test.com',
            'first_name': 'Test',
            'last_name': 'Teacher',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'teacher'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get().role, 'teacher')
        
    def test_login(self):
        User.objects.create_user(
            username='testuser', 
            email='test@test.com', 
            password='testpass123',
            role='student'
        )
        url = reverse('login')
        data = {
            'email': 'test@test.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

class CourseTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher', 
            email='teacher@test.com', 
            password='testpass123',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student', 
            email='student@test.com', 
            password='testpass123',
            role='student'
        )
        self.client = APIClient()
        
    def test_create_course_as_teacher(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('course-list')
        data = {
            'title': 'Test Course',
            'description': 'Test Description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Course.objects.get().created_by, self.teacher)
        
    def test_create_course_as_student_fails(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('course-list')
        data = {
            'title': 'Test Course',
            'description': 'Test Description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class PermissionTests(APITestCase):
    def setUp(self):
        self.teacher1 = User.objects.create_user(
            username='teacher1', 
            email='teacher1@test.com', 
            password='testpass123',
            role='teacher'
        )
        self.teacher2 = User.objects.create_user(
            username='teacher2', 
            email='teacher2@test.com', 
            password='testpass123',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student', 
            email='student@test.com', 
            password='testpass123',
            role='student'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            created_by=self.teacher1
        )
        self.course.teachers.add(self.teacher1)
        
        self.client = APIClient()
        
    def test_teacher_access_own_course(self):
        self.client.force_authenticate(user=self.teacher1)
        url = reverse('course-detail', kwargs={'pk': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_teacher_no_access_other_course(self):
        self.client.force_authenticate(user=self.teacher2)
        url = reverse('course-detail', kwargs={'pk': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class HomeworkSubmissionTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher', 
            email='teacher@test.com', 
            password='testpass123',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student', 
            email='student@test.com', 
            password='testpass123',
            role='student'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            created_by=self.teacher
        )
        self.course.teachers.add(self.teacher)
        self.course.students.add(self.student)
        
        self.lecture = Lecture.objects.create(
            title='Test Lecture',
            topic='Test Topic',
            course=self.course,
            order=1
        )
        
        self.assignment = HomeworkAssignment.objects.create(
            title='Test Assignment',
            description='Test Description',
            lecture=self.lecture
        )
        
        self.client = APIClient()
        
    def test_student_submit_homework(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('homework-submission-list')
        data = {
            'assignment': self.assignment.id,
            'submission_text': 'My homework submission'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HomeworkSubmission.objects.count(), 1)
        
    def test_teacher_grade_submission(self):
        # First create a submission
        submission = HomeworkSubmission.objects.create(
            student=self.student,
            assignment=self.assignment,
            submission_text='Test submission'
        )
        
        self.client.force_authenticate(user=self.teacher)
        url = reverse('grade-list')
        data = {
            'submission': submission.id,
            'grade_value': 85.5,
            'comments': 'Good work!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Grade.objects.count(), 1)
        self.assertEqual(Grade.objects.get().grade_value, 85.5)

class ModelTests(TestCase):
    def test_course_creation(self):
        teacher = User.objects.create_user(
            username='teacher', 
            email='teacher@test.com', 
            password='testpass123',
            role='teacher'
        )
        course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            created_by=teacher
        )
        self.assertEqual(str(course), 'Test Course')
        
    def test_lecture_creation(self):
        teacher = User.objects.create_user(
            username='teacher', 
            email='teacher@test.com', 
            password='testpass123',
            role='teacher'
        )
        course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            created_by=teacher
        )
        lecture = Lecture.objects.create(
            title='Test Lecture',
            topic='Test Topic',
            course=course,
            order=1
        )
        self.assertEqual(str(lecture), 'Test Course - Test Lecture')