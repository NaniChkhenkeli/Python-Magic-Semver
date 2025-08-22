from rest_framework import viewsets, status, permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
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
from rest_framework.exceptions import PermissionDenied


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
        else:  # student
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
        else:  # student
            return Lecture.objects.filter(course__students=user)
    
    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        user = self.request.user
        
        if user.role != 'teacher':
            raise permissions.PermissionDenied("Only teachers can create lectures")
        
        if user != course.created_by and user not in course.teachers.all():
            raise permissions.PermissionDenied("You can only create lectures for your own courses")
        
        serializer.save()

class HomeworkAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCourseTeacherOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return HomeworkAssignment.objects.filter(
                models.Q(lecture__course__created_by=user) | 
                models.Q(lecture__course__teachers=user)
            ).distinct()
        else:  # student
            return HomeworkAssignment.objects.filter(lecture__course__students=user)
    
    def perform_create(self, serializer):
        lecture = serializer.validated_data['lecture']
        user = self.request.user
        
        if user.role != 'teacher':
            raise permissions.PermissionDenied("Only teachers can create homework assignments")
        
        if user != lecture.course.created_by and user not in lecture.course.teachers.all():
            raise permissions.PermissionDenied("You can only create homework for your own courses")
        
        serializer.save()

class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubmissionOwnerOrTeacher]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return HomeworkSubmission.objects.filter(
                models.Q(assignment__lecture__course__created_by=user) |
                models.Q(assignment__lecture__course__teachers=user)
            ).distinct()
        else:  # student
            return HomeworkSubmission.objects.filter(student=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        assignment = serializer.validated_data['assignment']
        
        if user.role != 'student':
            raise permissions.PermissionDenied("Only students can submit homework")
        
        if user not in assignment.lecture.course.students.all():
            raise permissions.PermissionDenied("You must be enrolled in the course to submit homework")
        
        if HomeworkSubmission.objects.filter(student=user, assignment=assignment).exists():
            raise serializers.ValidationError("You have already submitted homework for this assignment")
        
        serializer.save(student=user)

class GradeViewSet(viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated, CanGradeSubmission]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return Grade.objects.filter(
                models.Q(submission__assignment__lecture__course__created_by=user) |
                models.Q(submission__assignment__lecture__course__teachers=user)
            ).distinct()
        else:  # student
            return Grade.objects.filter(submission__student=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        submission = serializer.validated_data['submission']
        
        if user.role != 'teacher':
            raise permissions.PermissionDenied("Only teachers can assign grades")
        
        course = submission.assignment.lecture.course
        if user != course.created_by and user not in course.teachers.all():
            raise permissions.PermissionDenied("You can only grade submissions for your own courses")
        
        serializer.save(graded_by=user)

class GradeCommentViewSet(viewsets.ModelViewSet):
    serializer_class = GradeCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'teacher':
            return GradeComment.objects.filter(
                models.Q(grade__submission__assignment__lecture__course__created_by=user) |
                models.Q(grade__submission__assignment__lecture__course__teachers=user)
            ).distinct()
        else:  
            return GradeComment.objects.filter(grade__submission__student=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        grade = serializer.validated_data['grade']
        
        if user.role == 'student':
            if grade.submission.student != user:
                raise permissions.PermissionDenied("You can only comment on your own grades")
        else:  # teacher
            course = grade.submission.assignment.lecture.course
            if user != course.created_by and user not in course.teachers.all():
                raise permissions.PermissionDenied("You can only comment on grades for your own courses")
        
        serializer.save(author=user)