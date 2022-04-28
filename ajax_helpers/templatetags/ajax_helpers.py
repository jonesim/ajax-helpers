import json
from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from ..utils import random_string
from ..html_include import html_include
register = template.Library()


@register.simple_tag(takes_context=True)
def lib_include(context, *args, **kwargs):
    request = context.get('request')
    legacy = False
    if request:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'Trident' in user_agent or 'MSIE' in user_agent:
            legacy = True
    include_str = ''
    if not args:
        include_str = html_include(cdn=kwargs.get('cdn'), module=kwargs.get('module'), legacy=legacy)
    for a in args:
        include_str += html_include(a, cdn=kwargs.get('cdn'), module=kwargs.get('module'), legacy=legacy)
    return mark_safe(include_str)


@register.simple_tag
def init_ajax():
    return mark_safe(f'<script src="{static("ajax_helpers/ajax_helpers.js")}"></script>')


def determine_css_class(bootstrap_style, css_class):
    if css_class:
        return css_class
    return 'btn ' + ' '.join(['btn-' + s.strip() for s in bootstrap_style.split(',')])


@register.simple_tag
def post_json_js(url_name=None, url_args=None, blob=False, **kwargs):
    json_data = {'data': kwargs}
    if url_name:
        json_data['url'] = reverse(url_name, args=url_args)
    if blob:
        json_data['response_type'] = 'blob'
    return mark_safe(f'ajax_helpers.post_json({json.dumps(json_data)})')


@register.simple_tag
def button_javascript(button_name, url_name=None, url_args=None, blob=False, **kwargs):
    return post_json_js(button=button_name, url_name=url_name, url_args=url_args, blob=blob, **kwargs)


@register.simple_tag
def ajax_button(text, name, bootstrap_style='primary', css_class=None, **kwargs):
    return mark_safe(f'''<button class="{determine_css_class(bootstrap_style, css_class) }"''' 
                     f'''onclick='{button_javascript(name, **kwargs) }'>{ text }</button>''')

@register.simple_tag
def ajax_method_button(text, method, bootstrap_style='primary', css_class=None, **kwargs):
    return mark_safe(f'''<button class="{determine_css_class(bootstrap_style, css_class) }"''' 
                     f'''onclick='{post_json_js(ajax_method=method, **kwargs) }'>{ text }</button>''')


@register.simple_tag
def send_form(form_id, **kwargs):
    kwargs.update({"form_id": form_id})
    return f'''ajax_helpers.send_form("{form_id}", {json.dumps(kwargs)})'''


@register.simple_tag
def send_form_button(text, form_id, bootstrap_style='primary', css_class=None, **kwargs):
    return mark_safe(f'''<button class="{ determine_css_class(bootstrap_style, css_class) }"''' 
                     f'''onclick='{send_form(form_id, **kwargs) }'>{ text }</button>''')


@register.inclusion_tag('ajax_helpers/upload_file.html')
def upload_file(text='Upload File', bootstrap_style='primary', css_class=None, drag_drop=None, width=None, height=None, progress=False):
    return {
        'id': random_string(),
        'text': text,
        'css_class': determine_css_class(bootstrap_style, css_class),
        'drag_drop': drag_drop,
        'width': width,
        'height': height,
        'progress': progress,
    }


@register.simple_tag
def tooltip_init(selector, function_name, placement='', template=''):
    return mark_safe(f"<script>ajax_helpers.tooltip('{selector}', '{function_name}', "
                     f"'{placement}', '{template}')</script>")


@register.inclusion_tag('ajax_helpers/ajax_timer.html')
def ajax_timer(name, interval_ms):
    return {
        'name': name,
        'interval': interval_ms
    }
