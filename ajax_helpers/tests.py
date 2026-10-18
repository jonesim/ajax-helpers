from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, override_settings

from .utils import is_ajax

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


class RequestHeaderTests(SimpleTestCase):
    """is_ajax() routes on X-Requested-With, so the client must send it to its own origin."""

    @staticmethod
    def first_inside(guard, statement):
        js = (Path(__file__).parent / 'static' / 'ajax_helpers' / 'ajax_helpers.js').read_text(encoding='utf-8')
        lines = [line.strip() for line in js.splitlines()]
        return any(lines[i] == f'if ({guard}) {{' and lines[i + 1] == statement for i in range(len(lines) - 1))

    def test_fetch_requests_send_it_to_their_own_origin(self):
        self.assertTrue(self.first_inside('same_origin(config.url)', "headers['X-Requested-With'] = 'XMLHttpRequest';"))

    def test_xhr_requests_send_it_to_their_own_origin(self):
        self.assertTrue(
            self.first_inside('same_origin(url)', "xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');")
        )

    def test_is_ajax_reads_it(self):
        self.assertTrue(is_ajax(RequestFactory().post('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')))
        self.assertFalse(is_ajax(RequestFactory().post('/')))
