"""Ajax handlers put to the project's permission check (``ajax_helpers.permissions``)."""

import json

from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.views import View

from .mixins import AjaxHelpers, ReceiveForm, ajax_method

CHECK = 'ajax_helpers.test_permissions.check'

ASKED = []
REFUSED = set()
RAN = []


def check(request, kind, name, obj=None):
    ASKED.append((kind, name))
    return (kind, name) not in REFUSED


class PageView(AjaxHelpers, View):
    def button_approve(self, **kwargs):
        RAN.append('approve')
        return JsonResponse([], safe=False)

    @ajax_method
    def save(self, **kwargs):
        RAN.append('save')
        return JsonResponse([], safe=False)


class FormView(ReceiveForm, View):
    def form_contact(self, **kwargs):
        RAN.append('contact')
        return JsonResponse([], safe=False)


def post_json(view, data):
    request = RequestFactory().post(
        '/', data=json.dumps(data), content_type='application/json', headers={'x-requested-with': 'XMLHttpRequest'}
    )
    return view.as_view()(request)


class PermissionCheckTestBase(SimpleTestCase):
    def setUp(self):
        ASKED.clear()
        REFUSED.clear()
        RAN.clear()


class WithNoCheckSetTests(PermissionCheckTestBase):
    def test_a_button_runs_as_before(self):
        post_json(PageView, {'button': 'approve'})

        self.assertEqual(RAN, ['approve'])


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
class WithACheckSetTests(PermissionCheckTestBase):
    def test_an_allowed_button_runs(self):
        post_json(PageView, {'button': 'approve'})

        self.assertEqual(RAN, ['approve'])
        self.assertIn(('button', 'approve'), ASKED)

    def test_a_refused_button_does_not_run_and_says_why(self):
        REFUSED.add(('button', 'approve'))

        response = post_json(PageView, {'button': 'approve'})

        self.assertEqual(RAN, [])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)[0]['function'], 'message')

    def test_a_refused_ajax_method_does_not_run(self):
        REFUSED.add(('ajax_method', 'save'))

        post_json(PageView, {'ajax_method': 'save'})

        self.assertEqual(RAN, [])

    def test_a_refused_form_post_does_not_run(self):
        REFUSED.add(('form', 'contact'))
        request = RequestFactory().post('/', data={'form_id': 'contact'}, headers={'x-requested-with': 'XMLHttpRequest'})

        response = FormView.as_view()(request)

        self.assertEqual(RAN, [])
        self.assertEqual(json.loads(response.content)[0]['function'], 'message')
