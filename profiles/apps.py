from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"

    def ready(self):
        # Import signal handlers to auto-create UserProfile objects
        from . import signals  # noqa: F401
