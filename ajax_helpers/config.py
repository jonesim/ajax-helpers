from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

SUPPORTED_FRAMEWORKS = ('bootstrap4', 'bootstrap5')


def get_css_framework():
    framework = getattr(settings, 'CSS_FRAMEWORK', 'bootstrap4')
    if framework not in SUPPORTED_FRAMEWORKS:
        raise ImproperlyConfigured(
            f"CSS_FRAMEWORK={framework!r} is not supported; choose one of {list(SUPPORTED_FRAMEWORKS)}")
    return framework
