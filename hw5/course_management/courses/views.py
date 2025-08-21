from rest_framework import viewsets, status, permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import User, Course, Lecture, HomeworkAssignment, HomeworkSubmission, Grade, GradeComment
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    CourseSerializer, LectureSerializer, HomeworkAssignmentSerializer,
    HomeworkSubmissionSerializer, GradeSerializer, GradeCommentSerializer
)
from django.db import models 
from .permissions import (
    IsTeacherOrReadOnly, IsCourseTeacherOrReadOnly, IsStudentOfCourse,
    IsSubmissionOwnerOrTeacher, CanGradeSubmission
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Login successful'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsCourseTeacherOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return Course.objects.filter(
                models.Q(created_by=user) | models.Q(teachers=user)
            ).distinct()
        else:
            return Course.objects.filter(
                models.Q(students=user) | models.Q(is_active=True)
            ).distinct()
    
    def perform_create(self, serializer):
        if self.request.user.role != 'teacher':
            raise PermissionDenied("Only teachers can create courses")
        course = serializer.save(created_by=self.request.user)
        course.teachers.add(self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Allow students to enroll themselves in a course"""
        course = self.get_object()
        user = request.user
        
        if user.role != 'student':
            return Response({'error': 'Only students can enroll in courses'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not course.is_active:
            return Response({'error': 'Course is not active'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user in course.students.all():
            return Response({'error': 'Already enrolled in this course'}, status=status.HTTP_400_BAD_REQUEST)
        
        course.students.add(user)
        return Response({'message': 'Successfully enrolled in course'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll_student(self, request, pk=None):
        """Allow teachers to enroll students"""
        course = self.get_object()
        student_id = request.data.get('student_id')
        
        if not student_id:
            return Response({'error': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = User.objects.get(id=student_id, role='student')
            if student in course.students.all():
                return Response({'error': 'Student already enrolled'}, status=status.HTTP_400_BAD_REQUEST)
            course.students.add(student)
            return Response({'message': f'Student {student.email} enrolled successfully'})
        except User.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def remove_student(self, request, pk=None):
        course = self.get_object()
        student_id = request.data.get('student_id')
        
        if not student_id:
            return Response({'error': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            student = User.objects.get(id=student_id, role='student')
            course.students.remove(student)
            return Response({'message': f'Student {student.email} removed successfully'})
        except User.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_teacher(self, request, pk=None):
        course = self.get_object()
        teacher_id = request.data.get('teacher_id')
        
        if not teacher_id:
            return Response({'error': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            teacher = User.objects.get(id=teacher_id, role='teacher')
            if teacher in course.teachers.all():
                return Response({'error': 'Teacher already added'}, status=status.HTTP_400_BAD_REQUEST)
            course.teachers.add(teacher)
            return Response({'message': f'Teacher {teacher.email} added successfully'})
        except User.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

class LectureViewSet(viewsets.ModelViewSet):
    serializer_class = LectureSerializer
    permission_classes = [permissions.IsAuthenticated, IsCourseTeacherOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return Lecture.objects.filter(
                models.Q(course__created_by=user) | models.Q(course__teachers=user)
            ).distinct()
        else:
            return Lecture.objects.filter(course__students=user)
    
    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        user = self.request.user
        
        if user.role != 'teacher':
            raise PermissionDenied("Only teachers can create lectures")
        
        if user != course.created_by and user not in course.teachers.all():
            raise PermissionDenied("You can only create lectures for your own courses")
        
        serializer.save()