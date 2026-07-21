#!/usr/bin/env python
"""Standalone test runner for django-ajax-helpers.

Configures a minimal Django environment (only ``ajax_helpers`` installed) so the
package's tests can run without the full example project / ecosystem. Usage::

    python runtests.py
"""
import sys

import django
from django.conf import settings


def main():
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=['django.contrib.staticfiles', 'ajax_helpers'],
        STATIC_URL='/static/',
        DATABASES={},
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {},
        }],
    )
    django.setup()

    from django.test.utils import get_runner

    test_runner = get_runner(settings)()
    failures = test_runner.run_tests(['ajax_helpers'])
    sys.exit(bool(failures))


if __name__ == '__main__':
    main()
