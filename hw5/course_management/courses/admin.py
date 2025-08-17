from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User, Course, Lecture, HomeworkAssignment, HomeworkSubmission, Grade, GradeComment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'get_full_name', 'role', 'is_staff', 'is_active', 'date_joined', 'last_login')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('email', 'first_name', 'last_name', 'role')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_active', 'students_count', 'teachers_count', 'lectures_count', 'created_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'created_by__email', 'created_by__username')
    filter_horizontal = ('teachers', 'students')
    readonly_fields = ('id', 'created_at', 'updated_at', 'lectures_count', 'homework_count')
    raw_id_fields = ('created_by',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'created_by', 'is_active')
        }),
        ('Participants', {
            'fields': ('teachers', 'students'),
        }),
        ('Statistics', {
            'fields': ('lectures_count', 'homework_count'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def students_count(self, obj):
        count = obj.students.count()
        url = reverse('admin:courses_user_changelist') + f'?enrolled_courses__id__exact={obj.id}&role__exact=student'
        return format_html('<a href="{}">{} students</a>', url, count)
    students_count.short_description = 'Students'
    
    def teachers_count(self, obj):
        count = obj.teachers.count()
        return f"{count} teachers"
    teachers_count.short_description = 'Teachers'
    
    def lectures_count(self, obj):
        count = obj.lectures.count()
        url = reverse('admin:courses_lecture_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}">{} lectures</a>', url, count)
    lectures_count.short_description = 'Lectures'
    
    def homework_count(self, obj):
        count = sum(lecture.homework_assignments.count() for lecture in obj.lectures.all())
        return f"{count} assignments"
    homework_count.short_description = 'Homework Assignments'


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_link', 'order', 'homework_count', 'has_presentation', 'created_at')
    list_filter = ('course', 'created_at', 'updated_at')
    search_fields = ('title', 'topic', 'course__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'homework_count')
    raw_id_fields = ('course',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'topic', 'course', 'order', 'presentation_file')
        }),
        ('Statistics', {
            'fields': ('homework_count',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def course_link(self, obj):
        url = reverse('admin:courses_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_link.short_description = 'Course'
    course_link.admin_order_field = 'course__title'
    
    def homework_count(self, obj):
        count = obj.homework_assignments.count()
        if count > 0:
            url = reverse('admin:courses_homeworkassignment_changelist') + f'?lecture__id__exact={obj.id}'
            return format_html('<a href="{}">{} assignments</a>', url, count)
        return "0 assignments"
    homework_count.short_description = 'Homework'
    
    def has_presentation(self, obj):
        return bool(obj.presentation_file)
    has_presentation.boolean = True
    has_presentation.short_description = 'Has Presentation'


@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lecture_link', 'course_name', 'due_date', 'submissions_count', 'created_at')
    list_filter = ('lecture__course', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'lecture__title', 'lecture__course__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'submissions_count')
    raw_id_fields = ('lecture',)
    date_hierarchy = 'due_date'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'lecture', 'due_date')
        }),
        ('Statistics', {
            'fields': ('submissions_count',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def lecture_link(self, obj):
        url = reverse('admin:courses_lecture_change', args=[obj.lecture.id])
        return format_html('<a href="{}">{}</a>', url, obj.lecture.title)
    lecture_link.short_description = 'Lecture'
    lecture_link.admin_order_field = 'lecture__title'
    
    def course_name(self, obj):
        return obj.lecture.course.title
    course_name.short_description = 'Course'
    course_name.admin_order_field = 'lecture__course__title'
    
    def submissions_count(self, obj):
        count = obj.submissions.count()
        if count > 0:
            url = reverse('admin:courses_homeworksubmission_changelist') + f'?assignment__id__exact={obj.id}'
            return format_html('<a href="{}">{} submissions</a>', url, count)
        return "0 submissions"
    submissions_count.short_description = 'Submissions'


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment_title', 'student_link', 'course_name', 'submitted_at', 'has_grade', 'grade_value')
    list_filter = ('assignment__lecture__course', 'submitted_at', 'grade__grade_value')
    search_fields = ('assignment__title', 'student__email', 'student__username', 'submission_text')
    readonly_fields = ('id', 'submitted_at', 'updated_at')
    raw_id_fields = ('student', 'assignment')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        (None, {
            'fields': ('assignment', 'student', 'submission_text')
        }),
        ('Timestamps', {
            'fields': ('id', 'submitted_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def assignment_title(self, obj):
        return obj.assignment.title
    assignment_title.short_description = 'Assignment'
    assignment_title.admin_order_field = 'assignment__title'
    
    def student_link(self, obj):
        url = reverse('admin:courses_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.email)
    student_link.short_description = 'Student'
    student_link.admin_order_field = 'student__email'
    
    def course_name(self, obj):
        return obj.assignment.lecture.course.title
    course_name.short_description = 'Course'
    course_name.admin_order_field = 'assignment__lecture__course__title'
    
    def has_grade(self, obj):
        return hasattr(obj, 'grade')
    has_grade.boolean = True
    has_grade.short_description = 'Graded'
    
    def grade_value(self, obj):
        if hasattr(obj, 'grade'):
            return f"{obj.grade.grade_value}%"
        return "-"
    grade_value.short_description = 'Grade'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('submission_info', 'student_name', 'grade_value', 'graded_by', 'comments_count', 'graded_at')
    list_filter = ('graded_at', 'grade_value', 'submission__assignment__lecture__course')
    search_fields = ('submission__student__email', 'submission__assignment__title', 'graded_by__email', 'comments')
    readonly_fields = ('id', 'graded_at', 'updated_at', 'comments_count')
    raw_id_fields = ('submission', 'graded_by')
    
    fieldsets = (
        (None, {
            'fields': ('submission', 'grade_value', 'comments', 'graded_by')
        }),
        ('Statistics', {
            'fields': ('comments_count',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('id', 'graded_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def submission_info(self, obj):
        return f"{obj.submission.assignment.title}"
    submission_info.short_description = 'Assignment'
    submission_info.admin_order_field = 'submission__assignment__title'
    
    def student_name(self, obj):
        student = obj.submission.student
        url = reverse('admin:courses_user_change', args=[student.id])
        name = f"{student.first_name} {student.last_name}".strip() or student.username
        return format_html('<a href="{}">{}</a>', url, name)
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'submission__student__email'
    
    def comments_count(self, obj):
        count = obj.discussion_comments.count()
        if count > 0:
            url = reverse('admin:courses_gradecomment_changelist') + f'?grade__id__exact={obj.id}'
            return format_html('<a href="{}">{} comments</a>', url, count)
        return "0 comments"
    comments_count.short_description = 'Comments'


@admin.register(GradeComment)
class GradeCommentAdmin(admin.ModelAdmin):
    list_display = ('grade_info', 'author_name', 'author_role', 'comment_preview', 'created_at')
    list_filter = ('created_at', 'author__role', 'grade__submission__assignment__lecture__course')
    search_fields = ('author__email', 'comment', 'grade__submission__student__email')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('grade', 'author')
    
    fieldsets = (
        (None, {
            'fields': ('grade', 'author', 'comment')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    
    def grade_info(self, obj):
        return f"Grade for {obj.grade.submission.student.email}"
    grade_info.short_description = 'Grade'
    
    def author_name(self, obj):
        author = obj.author
        url = reverse('admin:courses_user_change', args=[author.id])
        name = f"{author.first_name} {author.last_name}".strip() or author.username
        return format_html('<a href="{}">{}</a>', url, name)
    author_name.short_description = 'Author'
    author_name.admin_order_field = 'author__email'
    
    def author_role(self, obj):
        return obj.author.get_role_display()
    author_role.short_description = 'Role'
    author_role.admin_order_field = 'author__role'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment Preview'