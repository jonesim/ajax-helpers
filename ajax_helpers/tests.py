from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import SimpleTestCase, override_settings

INCLUDE = ("{% load ajax_helpers %}"
           "{% lib_include 'ajax_helpers' 'Bootstrap' module='ajax_helpers.includes' %}")


def render_includes():
    return Template(INCLUDE).render(Context({}))


class CssFrameworkIncludeTests(SimpleTestCase):

    def assert_bootstrap4(self, html):
        # jQuery + Popper bundled, Bootstrap 4 served from local static
        self.assertIn('jquery.min.js', html)
        self.assertIn('popper.min.js', html)
        self.assertIn('ajax_helpers.js', html)
        self.assertIn('/static/ajax_helpers/js/bootstrap.min.js', html)
        self.assertIn('/static/ajax_helpers/css/bootstrap.min.css', html)

    def test_default_is_bootstrap4(self):
        self.assert_bootstrap4(render_includes())

    @override_settings(CSS_FRAMEWORK='bootstrap4')
    def test_explicit_bootstrap4(self):
        self.assert_bootstrap4(render_includes())

    @override_settings(CSS_FRAMEWORK='bootstrap5')
    def test_bootstrap5_drops_jquery_and_serves_bs5_from_cdn(self):
        html = render_includes()
        self.assertIn('ajax_helpers.js', html)
        self.assertNotIn('jquery', html)
        self.assertNotIn('popper', html)
        self.assertIn('cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js', html)
        self.assertIn('cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css', html)

    @override_settings(CSS_FRAMEWORK='tailwind')
    def test_unsupported_framework_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            render_includes()
