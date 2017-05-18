import django.apps

class EDTFConfig(django.apps.AppConfig):
    name = 'edtf'
    def ready(self):
        import signals
