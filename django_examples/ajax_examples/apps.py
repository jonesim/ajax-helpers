from show_src_code.apps import PypiAppConfig


class AjaxConfig(PypiAppConfig):
    default = True
    name = 'ajax_examples'
    pypi = 'django-ajax-helpers'
    urls = 'ajax_examples.urls'
