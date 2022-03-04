import string
import random


def random_string():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _i in range(8))


def ajax_command(function_name, **kwargs):
    if type(function_name) == dict:
        return function_name
    else:
        kwargs['function'] = function_name
        return kwargs


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
