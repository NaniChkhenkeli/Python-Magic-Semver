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
    email = serializers.EmailField()  
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)  
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
    is_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'created_by', 'teachers', 'students', 
                 'student_count', 'is_active', 'is_enrolled', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_count(self, obj):
        return obj.students.count()
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'student':
                return request.user in obj.students.all()
            elif request.user.role == 'teacher':
                return request.user in obj.teachers.all() or request.user == obj.created_by
        return False

class LectureSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Lecture
        fields = ['id', 'title', 'topic', 'presentation_file', 'course', 'course_title', 
                 'order', 'can_edit', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'teacher':
            return (request.user == obj.course.created_by or 
                   request.user in obj.course.teachers.all())
        return False
    
    def validate_course(self, value):
        request = self.context.get('request')
        if request and request.user.role == 'teacher':
            if (request.user != value.created_by and 
                request.user not in value.teachers.all()):
                raise serializers.ValidationError("You can only create lectures for your own courses")
        return value

class HomeworkAssignmentSerializer(serializers.ModelSerializer):
    lecture_title = serializers.CharField(source='lecture.title', read_only=True)
    course_title = serializers.CharField(source='lecture.course.title', read_only=True)
    has_submitted = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = HomeworkAssignment
        fields = ['id', 'title', 'description', 'lecture', 'lecture_title', 'course_title',
                 'due_date', 'has_submitted', 'can_edit', 'created_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_has_submitted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            return HomeworkSubmission.objects.filter(
                assignment=obj, student=request.user
            ).exists()
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'teacher':
            course = obj.lecture.course
            return (request.user == course.created_by or 
                   request.user in course.teachers.all())
        return False
    
    def validate_lecture(self, value):
        request = self.context.get('request')
        if request and request.user.role == 'teacher':
            course = value.course
            if (request.user != course.created_by and 
                request.user not in course.teachers.all()):
                raise serializers.ValidationError("You can only create homework for your own courses")
        return value

class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    course_title = serializers.CharField(source='assignment.lecture.course.title', read_only=True)
    has_grade = serializers.SerializerMethodField()
    
    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'assignment', 'assignment_title', 'course_title', 'student', 
                 'submission_text', 'has_grade', 'submitted_at']
        read_only_fields = ['id', 'student', 'submitted_at', 'updated_at']
    
    def get_has_grade(self, obj):
        return hasattr(obj, 'grade')
    
    def validate_assignment(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'student':
            if request.user not in value.lecture.course.students.all():
                raise serializers.ValidationError("You must be enrolled in the course to submit homework")
            
            if HomeworkSubmission.objects.filter(assignment=value, student=request.user).exists():
                raise serializers.ValidationError("You have already submitted homework for this assignment")
        
        return value

class GradeSerializer(serializers.ModelSerializer):
    graded_by = UserSerializer(read_only=True)
    student_email = serializers.CharField(source='submission.student.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    assignment_title = serializers.CharField(source='submission.assignment.title', read_only=True)
    course_title = serializers.CharField(source='submission.assignment.lecture.course.title', read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Grade
        fields = ['id', 'submission', 'grade_value', 'comments', 'graded_by', 
                 'student_email', 'student_name', 'assignment_title', 'course_title',
                 'can_edit', 'graded_at']
        read_only_fields = ['id', 'graded_by', 'graded_at', 'updated_at']
    
    def get_student_name(self, obj):
        student = obj.submission.student
        return f"{student.first_name} {student.last_name}".strip() or student.username
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.role == 'teacher':
            course = obj.submission.assignment.lecture.course
            return (request.user == course.created_by or 
                   request.user in course.teachers.all())
        return False
    
    def validate_submission(self, value):
        request = self.context.get('request')
        if request and request.user.role == 'teacher':
            course = value.assignment.lecture.course
            if (request.user != course.created_by and 
                request.user not in course.teachers.all()):
                raise serializers.ValidationError("You can only grade submissions for your own courses")
        return value
    
    def validate_grade_value(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Grade must be between 0 and 100")
        return value

class GradeCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_name = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = GradeComment
        fields = ['id', 'grade', 'author', 'author_name', 'comment', 'can_delete', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']
    
    def get_author_name(self, obj):
        author = obj.author
        return f"{author.first_name} {author.last_name}".strip() or author.username
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if obj.author == request.user:
                return True
            if request.user.role == 'teacher':
                course = obj.grade.submission.assignment.lecture.course
                return (request.user == course.created_by or 
                       request.user in course.teachers.all())
        return False
    
    def validate_grade(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            course = value.submission.assignment.lecture.course
            
            if request.user.role == 'student':
                if value.submission.student != request.user:
                    raise serializers.ValidationError("You can only comment on your own grades")
            
            elif request.user.role == 'teacher':
                if (request.user != course.created_by and 
                    request.user not in course.teachers.all()):
                    raise serializers.ValidationError("You can only comment on grades for your own courses")
        
        return value