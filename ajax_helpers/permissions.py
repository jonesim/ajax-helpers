"""Asking the project whether an ajax request may run.

A project names one function in ``settings.DJANGO_ADVANCED_PERMISSION_CHECK`` (a dotted path)::

    def check(request, kind, name, obj=None) -> bool

Before a view runs the handler an ajax post asks for, the function is asked with the command type
as ``kind`` and the handler's name as ``name``: ``('button', 'approve')`` before ``button_approve``,
``('ajax_method', 'save')`` before an ``@ajax_method``, ``('form', <form_id>)``, ``('upload',
<name>)`` and ``('file_upload', 'ajax_file')`` for the others. ``obj`` is the view. Reads go through
it too (``tooltip``, ``select2``, ``timer``...), so the project decides which kinds it cares about.

The same setting and signature are read by django-advanced-menus, django-advanced-modals and
django-advanced-datatables, each with a ``kind`` of its own. With it unset everything runs.
"""

from django.conf import settings
from django.utils.module_loading import import_string

SETTING = 'DJANGO_ADVANCED_PERMISSION_CHECK'


def is_permitted(request, kind, name, obj=None):
    path = getattr(settings, SETTING, None)
    if not path:
        return True
    return bool(import_string(path)(request, kind, name, obj))


def refusal(view, kind, name):
    """The response to send instead of running the handler, or None to run it.

    Views without ``ajax_permission`` (a ``ReceiveForm`` used on its own) are asked directly.
    """
    check = getattr(view, 'ajax_permission', None)
    allowed = check(kind, name) if check else is_permitted(getattr(view, 'request', None), kind, name, view)
    if allowed:
        return None
    denied = getattr(view, 'ajax_permission_denied', None)
    if denied:
        return denied(kind, name)
    from django.http import JsonResponse

    return JsonResponse([{'function': 'message', 'text': PERMISSION_DENIED_MESSAGE}], safe=False)


PERMISSION_DENIED_MESSAGE = 'You do not have permission to do this.'
