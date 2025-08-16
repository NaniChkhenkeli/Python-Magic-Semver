from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Course, Lecture, HomeworkAssignment, HomeworkSubmission, Grade, GradeComment

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()  # Changed from username to email
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)  # Django's authenticate uses username parameter
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']

class CourseSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    teachers = UserSerializer(many=True, read_only=True)
    students = UserSerializer(many=True, read_only=True)
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'created_by', 'teachers', 'students', 'student_count', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_count(self, obj):
        return obj.students.count()

class LectureSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Lecture
        fields = ['id', 'title', 'topic', 'presentation_file', 'course', 'course_title', 'order', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class HomeworkAssignmentSerializer(serializers.ModelSerializer):
    lecture_title = serializers.CharField(source='lecture.title', read_only=True)
    
    class Meta:
        model = HomeworkAssignment
        fields = ['id', 'title', 'description', 'lecture', 'lecture_title', 'due_date', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'assignment', 'assignment_title', 'student', 'submission_text', 'submitted_at']
        read_only_fields = ['id', 'student', 'submitted_at', 'updated_at']

class GradeSerializer(serializers.ModelSerializer):
    graded_by = UserSerializer(read_only=True)
    student_email = serializers.CharField(source='submission.student.email', read_only=True)
    assignment_title = serializers.CharField(source='submission.assignment.title', read_only=True)
    
    class Meta:
        model = Grade
        fields = ['id', 'submission', 'grade_value', 'comments', 'graded_by', 'student_email', 'assignment_title', 'graded_at']
        read_only_fields = ['id', 'graded_by', 'graded_at', 'updated_at']

class GradeCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = GradeComment
        fields = ['id', 'grade', 'author', 'comment', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']