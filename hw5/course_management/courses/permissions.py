from rest_framework import permissions
from .models import Course, Lecture, HomeworkAssignment, HomeworkSubmission, Grade

class IsTeacherOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == 'teacher'

class IsCourseTeacherOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Course):
            course = obj
        elif hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'lecture'):
            course = obj.lecture.course
        elif hasattr(obj, 'assignment'):
            course = obj.assignment.lecture.course
        elif hasattr(obj, 'submission'):
            course = obj.submission.assignment.lecture.course
        else:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return (request.user in course.teachers.all() or 
                   request.user in course.students.all() or
                   request.user == course.created_by)
        
        return (request.user in course.teachers.all() or 
               request.user == course.created_by)

class IsStudentOfCourse(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, HomeworkAssignment):
            course = obj.lecture.course
        elif isinstance(obj, HomeworkSubmission):
            course = obj.assignment.lecture.course
        else:
            return False
        
        return (request.user in course.students.all() or
               request.user in course.teachers.all() or
               request.user == course.created_by)

class IsSubmissionOwnerOrTeacher(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        course = obj.assignment.lecture.course
        
        # Students can only access their own submissions
        if request.user.role == 'student':
            return obj.student == request.user
        
        # Teachers can access all submissions in their courses
        return (request.user in course.teachers.all() or 
               request.user == course.created_by)

class CanGradeSubmission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, HomeworkSubmission):
            course = obj.assignment.lecture.course
        elif isinstance(obj, Grade):
            course = obj.submission.assignment.lecture.course
        else:
            return False
        
        return (request.user in course.teachers.all() or 
               request.user == course.created_by)