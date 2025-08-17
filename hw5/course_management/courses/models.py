from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', _('Teacher')),
        ('student', _('Student')),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(_('role'), max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

class Course(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    created_by = models.ForeignKey(
        User,
        verbose_name=_('created by'),
        on_delete=models.CASCADE,
        related_name='created_courses'
    )
    teachers = models.ManyToManyField(
        User,
        verbose_name=_('teachers'),
        related_name='teaching_courses',
        limit_choices_to={'role': 'teacher'}
    )
    students = models.ManyToManyField(
        User,
        verbose_name=_('students'),
        related_name='enrolled_courses',
        limit_choices_to={'role': 'student'},
        blank=True
    )
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('course')
        verbose_name_plural = _('courses')
    
    def __str__(self):
        return self.title

class Lecture(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    topic = models.TextField(_('topic'))
    presentation_file = models.FileField(
        _('presentation file'),
        upload_to='presentations/',
        null=True,
        blank=True
    )
    course = models.ForeignKey(
        Course,
        verbose_name=_('course'),
        on_delete=models.CASCADE,
        related_name='lectures'
    )
    order = models.PositiveIntegerField(_('order'), default=1)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        verbose_name = _('lecture')
        verbose_name_plural = _('lectures')
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class HomeworkAssignment(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    lecture = models.ForeignKey(
        Lecture,
        verbose_name=_('lecture'),
        on_delete=models.CASCADE,
        related_name='homework_assignments',
        help_text=_('Select the lecture this assignment belongs to')
    )
    due_date = models.DateTimeField(
        _('due date'),
        null=True,
        blank=True,
        help_text=_('Format: YYYY-MM-DD HH:MM')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('homework assignment')
        verbose_name_plural = _('homework assignments')
    
    def __str__(self):
        return f"{self.lecture.title} - {self.title}"

class HomeworkSubmission(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        User,
        verbose_name=_('student'),
        on_delete=models.CASCADE,
        related_name='homework_submissions'
    )
    assignment = models.ForeignKey(
        HomeworkAssignment,
        verbose_name=_('assignment'),
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    submission_text = models.TextField(_('submission text'))
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        unique_together = ['student', 'assignment']
        ordering = ['-submitted_at']
        verbose_name = _('homework submission')
        verbose_name_plural = _('homework submissions')
    
    def __str__(self):
        return f"{self.student.email} - {self.assignment.title}"

class Grade(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(
        HomeworkSubmission,
        verbose_name=_('submission'),
        on_delete=models.CASCADE,
        related_name='grade'
    )
    grade_value = models.FloatField(
        _('grade value'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    comments = models.TextField(_('comments'), blank=True)
    graded_by = models.ForeignKey(
        User,
        verbose_name=_('graded by'),
        on_delete=models.CASCADE,
        related_name='assigned_grades'
    )
    graded_at = models.DateTimeField(_('graded at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('grade')
        verbose_name_plural = _('grades')
    
    def __str__(self):
        return f"{self.submission.student.email} - {self.grade_value}"

class GradeComment(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    grade = models.ForeignKey(
        Grade,
        verbose_name=_('grade'),
        on_delete=models.CASCADE,
        related_name='discussion_comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name=_('author'),
        on_delete=models.CASCADE
    )
    comment = models.TextField(_('comment'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('grade comment')
        verbose_name_plural = _('grade comments')
    
    def __str__(self):
        return f"Comment by {self.author.email} on grade {self.grade.id}"