from .config import get_css_framework
from .html_include import SourceBase, pip_version

version = pip_version('django-ajax-helpers')


class Jquery(SourceBase):
    static_path = 'ajax_helpers/'
    cdn_path = 'ajax.googleapis.com/ajax/libs/jquery/3.6.0/'
    cdn_js_path = ''
    js_filename = 'jquery.min.js'


class AjaxHelpers(SourceBase):
    static_path = 'ajax_helpers/'
    js_filename = 'ajax_helpers.js'
    legacy_js = 'ajax_helpers_legacy.js'
    js_path = ''
    css_filename = 'ajax_helpers.css'
    css_path = ''


class Popper(SourceBase):
    static_path = 'ajax_helpers/'
    cdn_path = 'cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.1/umd/'
    cdn_js_path = ''
    js_filename = 'popper.min.js'


class Bootstrap(SourceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if get_css_framework() == 'bootstrap5':
            self.static_path = None                                     # no local files -> forces CDN
            self.cdn_path = 'cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/'
            self.js_filename = 'bootstrap.bundle.min.js'                # Popper bundled in
            self.css_filename = 'bootstrap.min.css'
        else:
            self.static_path = 'ajax_helpers/'                          # unchanged BS4 behaviour
            self.cdn_path = 'cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/'
            self.filename = 'bootstrap.min'


class FontAwesome(SourceBase):
    static_path = 'ajax_helpers/fontawesome/'
    cdn_path = 'use.fontawesome.com/releases/v5.15.4/'
    css_filename = 'all.css'


class ScreenCapture(SourceBase):
    static_path = 'ajax_helpers/'
    js_filename = 'screen_capture.js'
    js_path = ''


def default_bundle():
    if get_css_framework() == 'bootstrap5':
        return [AjaxHelpers]
    return [Jquery, Popper, AjaxHelpers]


packages = {
    'ajax_helpers': default_bundle,   # callable, resolved at render time
}
