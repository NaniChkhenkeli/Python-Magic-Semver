from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


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
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email


class Course(models.Model):
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    instructor = models.ForeignKey(
        User,
        verbose_name=_('instructor'),
        on_delete=models.CASCADE,
        related_name='taught_courses',
        limit_choices_to={'role': 'teacher'}
    )
    additional_teachers = models.ManyToManyField(
        User,
        verbose_name=_('additional teachers'),
        related_name='co_taught_courses',
        limit_choices_to={'role': 'teacher'},
        blank=True
    )
    max_students = models.PositiveIntegerField(_('maximum students'), default=50)
    is_active = models.BooleanField(_('is active'), default=True)
    start_date = models.DateField(_('start date'), null=True, blank=True)
    end_date = models.DateField(_('end date'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('course')
        verbose_name_plural = _('courses')
    
    def __str__(self):
        return self.title
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date cannot be after end date.')
    
    @property
    def all_teachers(self):
        teacher_ids = [self.instructor.id]
        teacher_ids.extend(list(self.additional_teachers.values_list('id', flat=True)))
        return User.objects.filter(id__in=teacher_ids)
    
    @property
    def student_count(self):
        return self.enrollments.filter(is_active=True).count()
    
    @property
    def is_full(self):
        return self.student_count >= self.max_students
    
    def can_enroll_student(self):
        return self.is_active and not self.is_full


class Enrollment(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(_('enrolled at'), auto_now_add=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    class Meta:
        unique_together = ['student', 'course']
        verbose_name = _('enrollment')
        verbose_name_plural = _('enrollments')
    
    def __str__(self):
        return f"{self.student} enrolled in {self.course.title}"


class Lecture(models.Model):
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    presentation_file = models.FileField(
        _('presentation file'),
        upload_to='lectures/presentations/',
        null=True,
        blank=True,
        help_text='Upload presentation slides (PDF, PPT, etc.)'
    )
    order = models.PositiveIntegerField(_('order'), default=1)
    is_published = models.BooleanField(_('is published'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        verbose_name = _('lecture')
        verbose_name_plural = _('lectures')
    
    def __str__(self):
        return f"{self.course.title} - Lecture {self.order}: {self.title}"
    
    @property
    def has_presentation(self):
        return bool(self.presentation_file)


class HomeworkAssignment(models.Model):
    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    due_date = models.DateTimeField(
        _('due date'),
        null=True,
        blank=True,
        help_text=_('Leave empty for no deadline')
    )
    max_points = models.PositiveIntegerField(_('maximum points'), default=100)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('homework assignment')
        verbose_name_plural = _('homework assignments')
    
    def __str__(self):
        return f"{self.lecture.title} - {self.title}"
    
    @property
    def is_past_due(self):
        if not self.due_date:
            return False
        from django.utils import timezone
        return timezone.now() > self.due_date


class HomeworkSubmission(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'role': 'student'}
    )
    assignment = models.ForeignKey(
        HomeworkAssignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    content = models.TextField(_('submission content'))
    attachment = models.FileField(
        _('attachment'),
        upload_to='homework/submissions/',
        null=True,
        blank=True,
        help_text='Optional file attachment'
    )
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        unique_together = ['student', 'assignment']
        ordering = ['-submitted_at']
        verbose_name = _('homework submission')
        verbose_name_plural = _('homework submissions')
    
    def __str__(self):
        return f"{self.student} - {self.assignment.title}"
    
    @property
    def is_late(self):
        if not self.assignment.due_date:
            return False
        return self.submitted_at > self.assignment.due_date
    
    @property
    def has_grade(self):
        return hasattr(self, 'grade')


class Grade(models.Model):
    submission = models.OneToOneField(
        HomeworkSubmission,
        on_delete=models.CASCADE,
        related_name='grade'
    )
    points_earned = models.FloatField(
        _('points earned'),
        validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(_('feedback'), blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='grades_given',
        limit_choices_to={'role': 'teacher'}
    )
    graded_at = models.DateTimeField(_('graded at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('grade')
        verbose_name_plural = _('grades')
    
    def __str__(self):
        return f"{self.submission.student} - {self.points_earned}/{self.submission.assignment.max_points}"
    
    @property
    def percentage(self):
        max_points = self.submission.assignment.max_points
        if max_points == 0:
            return 0
        return round((self.points_earned / max_points) * 100, 2)
    
    def clean(self):
        if self.points_earned > self.submission.assignment.max_points:
            raise ValidationError('Points earned cannot exceed maximum points for assignment.')


class GradeComment(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(_('comment'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('grade comment')
        verbose_name_plural = _('grade comments')
    
    def __str__(self):
        return f"Comment by {self.author} on {self.grade}"