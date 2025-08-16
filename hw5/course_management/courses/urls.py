from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'lectures', views.LectureViewSet, basename='lecture')
router.register(r'homework-assignments', views.HomeworkAssignmentViewSet, basename='homework-assignment')
router.register(r'homework-submissions', views.HomeworkSubmissionViewSet, basename='homework-submission')
router.register(r'grades', views.GradeViewSet, basename='grade')
router.register(r'grade-comments', views.GradeCommentViewSet, basename='grade-comment')

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    
    path('', include(router.urls)),
]