from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    verbose_name = 'Learning Management System'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        This method is called when Django starts.
        """
        pass