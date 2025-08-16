from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Course, Lecture, HomeworkAssignment, HomeworkSubmission, Grade, GradeComment

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_staff', 'created_at')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role',)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('email', 'role')}),
    )

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_active', 'created_at', 'students_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'created_by__email')
    filter_horizontal = ('teachers', 'students')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = 'Students Count'

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'topic', 'course__title')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lecture', 'due_date', 'created_at', 'submissions_count')
    list_filter = ('lecture__course', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'lecture__title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def submissions_count(self, obj):
        return obj.submissions.count()
    submissions_count.short_description = 'Submissions Count'

@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'has_grade')
    list_filter = ('assignment__lecture__course', 'submitted_at')
    search_fields = ('assignment__title', 'student__email', 'student__username')
    readonly_fields = ('id', 'submitted_at', 'updated_at')
    
    def has_grade(self, obj):
        return hasattr(obj, 'grade')
    has_grade.boolean = True
    has_grade.short_description = 'Graded'

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('submission', 'grade_value', 'graded_by', 'graded_at')
    list_filter = ('graded_at', 'submission__assignment__lecture__course')
    search_fields = ('submission__student__email', 'submission__assignment__title', 'graded_by__email')
    readonly_fields = ('id', 'graded_at', 'updated_at')

@admin.register(GradeComment)
class GradeCommentAdmin(admin.ModelAdmin):
    list_display = ('grade', 'author', 'created_at', 'comment_preview')
    list_filter = ('created_at', 'author__role')
    search_fields = ('author__email', 'comment')
    readonly_fields = ('id', 'created_at')
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment Preview'