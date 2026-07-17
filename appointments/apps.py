from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "appointments"

    def ready(self):
        import appointments.signals