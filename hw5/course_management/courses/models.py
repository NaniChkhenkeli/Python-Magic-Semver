from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class User(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_courses')
    teachers = models.ManyToManyField(User, related_name='teaching_courses', 
                                    limit_choices_to={'role': 'teacher'})
    students = models.ManyToManyField(User, related_name='enrolled_courses', 
                                    limit_choices_to={'role': 'student'}, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Lecture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    topic = models.TextField()
    presentation_file = models.FileField(upload_to='presentations/', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class HomeworkAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='homework_assignments')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.lecture.title} - {self.title}"

class HomeworkSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homework_submissions')
    assignment = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE, related_name='submissions')
    submission_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'assignment']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.assignment.title}"

class Grade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(HomeworkSubmission, on_delete=models.CASCADE, related_name='grade')
    grade_value = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    comments = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_grades')
    graded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.submission.student.email} - {self.grade_value}"

class GradeComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='discussion_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.email} on grade {self.grade.id}"