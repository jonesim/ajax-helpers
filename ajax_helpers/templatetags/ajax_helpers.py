import json
from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from ..utils import random_string

register = template.Library()


@register.simple_tag
def init_ajax():
    return mark_safe(f'<script src="{static("ajax_helpers/ajax_helpers.js")}"></script>')


def determine_css_class(bootstrap_style, css_class):
    if css_class:
        return css_class
    return 'btn ' + ' '.join(['btn-' + s.strip() for s in bootstrap_style.split(',')])


@register.simple_tag
def button_javascript(button_name, url_name=None, url_args=None, **kwargs):
    json_data = {'data': dict(button=button_name, **kwargs)}
    if url_name:
        json_data['url'] = reverse(url_name, args=url_args)
    return f'ajax_helpers.post_json({json.dumps(json_data)})'


@register.simple_tag
def ajax_button(text, name, bootstrap_style='primary', css_class=None, **kwargs):
    return mark_safe(f'''<button class="{determine_css_class(bootstrap_style, css_class) }"''' 
                     f'''onclick='{button_javascript(name, **kwargs) }'>{ text }</button>''')


@register.simple_tag
def send_form(form_id, **kwargs):
    kwargs.update({"form_id": form_id})
    return f'''ajax_helpers.send_form("{form_id}", {json.dumps(kwargs)})'''


@register.simple_tag
def send_form_button(text, form_id, bootstrap_style='primary', css_class=None, **kwargs):
    return mark_safe(f'''<button class="{ determine_css_class(bootstrap_style, css_class) }"''' 
                     f'''onclick='{send_form(form_id, **kwargs) }'>{ text }</button>''')


@register.inclusion_tag('ajax_helpers/upload_file.html')
def upload_file(text='Upload File', bootstrap_style='primary', css_class=None):
    return {
        'id': random_string(),
        'text': text,
        'css_class': determine_css_class(bootstrap_style, css_class),
    }


@register.simple_tag
def tooltip_init(element_id, url_name, css_class='ajax-tooltip'):
    return mark_safe(
        f'''<script>ajax_helpers.tooltip.init('{element_id}', "{reverse(url_name)}", "{css_class}")</script>'''
    )


@register.inclusion_tag('ajax_helpers/ajax_timer.html')
def ajax_timer(name, interval_ms):
    return {
        'name': name,
        'interval': interval_ms
    }
