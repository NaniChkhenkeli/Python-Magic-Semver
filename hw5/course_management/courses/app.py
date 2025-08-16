from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Learning Management System Core'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        This method is called when Django starts.
        """
       
        pass