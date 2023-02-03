import string
import random

from django.template.loader import render_to_string


def random_string():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _i in range(8))


def ajax_command(function_name, **kwargs):
    if type(function_name) == dict:
        return function_name
    else:
        kwargs['function'] = function_name
        return kwargs


def toast_commands(*, text, header=None, header_small=None, html_id=None, position='bottom-right',
                   template_name='ajax_helpers/toast.html', header_classes='', body_classes='', auto_hide=True,
                   delay=None, font_awesome=None, show_hidden=False, extra_context=None):
    container_id = 'toast-{}'.format(position)
    container_html = '<div id="{}" style="position:fixed; {}:10px; {}:10px"></div>'.format(container_id,
                                                                                           *position.split('-'))
    if not delay and auto_hide:
        delay = 4000
    context = {'text': text,
               'header': header,
               'html_id': html_id if html_id else random_string(),
               'header_small': header_small,
               'header_classes': header_classes,
               'body_classes': body_classes,
               'auto_hide': auto_hide,
               'delay': delay,
               'font_awesome': font_awesome}
    if extra_context is not None:
        context = {**context, **extra_context}

    commands = [
        ajax_command('if_not_selector', selector='#' + container_id, commands=[
            ajax_command('append_to', selector='body', html=container_html)
        ])]
    if show_hidden:
        commands.append(ajax_command('remove', selector='#' + context['html_id'] + ':hidden'))
    commands.append(
        ajax_command('if_not_selector',
                     selector='#' + context['html_id'],
                     is_visible=show_hidden,
                     commands=[ajax_command('append_to', selector='#' + container_id,
                                            html=render_to_string(template_name=template_name, context=context))])
    )
    return commands


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
