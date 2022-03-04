import base64
import datetime
import os
from io import BytesIO

from django import forms
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django_menus.menu import MenuMixin
from openpyxl import Workbook
from show_src_code.view_mixins import DemoViewMixin

from ajax_helpers.mixins import AjaxHelpers, ReceiveForm, AjaxFileUploadMixin
from ajax_helpers.screen_capture import ScreenCaptureMixin
from ajax_helpers.utils import ajax_command


class DemoScreenCapture(ScreenCaptureMixin):

    def ajax_upload_video(self, **_kwargs):
        filename = 'screen_capture.mp4'
        path = '/media/' + filename
        with open(path, 'wb+') as destination:
            destination.write(self.request.FILES['data'].read())
        self.add_command('message', text='Uploaded')
        return self.command_response('redirect', url=self.request.path)


class MainMenu(DemoScreenCapture, DemoViewMixin, MenuMixin, TemplateView):

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('main_menu').add_items(
            ('ajax_main', 'General'),
            ('timer_examples', 'Timers'),
            ('toast_examples', 'Toast'),
            ('download_examples', 'File Downloads'),
            ('dragdrop_upload', 'File Uploads'),
            ('event_example', 'Event'),
            'help',
        )


class TestForm(forms.Form):
    text_entry = forms.CharField(max_length=100)


class ToolTip(TemplateView):
    template_name = 'ajax_examples/tooltip_template.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET['django'] == 'today':
            context['time'] = datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')
            context['day'] = 'Today'
        else:
            context['time'] = (datetime.datetime.now()-datetime.timedelta(days=1)).strftime('%m/%d/%Y, %H:%M:%S')
            context['day'] = 'Yesterday'
        return context


class Example1(ReceiveForm, AjaxHelpers, MainMenu):

    template_name = 'ajax_examples/main.html'

    def button_redirect(self):
        self.add_command('message', text='Will redirect after this message')
        self.add_command('redirect', url=reverse('redirect'))
        return self.command_response()

    def button_test_clipboard(self):
        self.add_command('clipboard', text='Text from Django')
        return self.command_response('message', text='Text copied to clipboard')

    def button_test_ajax(self):
        return self.command_response('message', text='From Django View')

    def button_test_html(self):
        return self.command_response('html', selector='#html_test', html='From Django View')

    def form_form_id(self, **kwargs):
        return self.command_response('message', text=f'From Django View - field {kwargs["field1"]}')

    def form_django_form_id(self, **kwargs):
        a = TestForm(kwargs)
        if a.is_valid():
            return self.command_response('html', selector='#django_form_id', html='thank you', parent=True)
        else:
            return self.command_response('html', selector='#django_form_id', html=a.as_p())

    def button_append(self):
        self.add_command('append_to', html='<div>New div</div>', selector='#append-to')
        return self.command_response()

    def button_css(self):
        self.add_command('set_css', selector='#css-test', prop='width', val='800px')
        return self.command_response('set_css', selector='#css-test', prop='background-color', val='yellow')

    def button_null(self):
        return self.command_response('null')

    def button_count(self):
        return self.command_response('element_count', selector='div', data={'ajax': 'count_response'})

    def ajax_count_response(self, **kwargs):
        return self.command_response('message', text='Number of divs ' + str(kwargs['count']))

    def button_get_attr(self):
        return self.command_response('get_attr', selector='#test-attr-div', attr='class',
                                     data={'ajax': 'attr_response'})

    def ajax_attr_response(self, **kwargs):
        return self.command_response('message', text='Div classes ' + str(kwargs['val']))

    def file_upload(self, file):
        return self.command_response('message', text=f'Received {file.name} size {file.size}')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TestForm()
        return context


class Example2(Example1):

    template_name = 'ajax_examples/redirect.html'


class TimerExample(Example1):
    template_name = 'ajax_examples/timer.html'

    def timer_test(self, **kwargs):
        return self.command_response('html', selector='#time_div',
                                     html=datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

    def get_context_data(self, **kwargs):

        self.add_page_command(
            'timeout', commands=[ajax_command('message', text='Message appears after 4 seconds')], time=4000
        )
        self.add_page_command(
            'timer', commands=[ajax_command('ajax_post', data={'timer': 'test'})], interval=2000
        )

        return super().get_context_data(**kwargs)


class ToastExample(Example1):
    template_name = 'ajax_examples/toast.html'

    def button_toast_simple(self):
        return self.command_response('toast', text='toast message', position='bottom-right')

    def button_toast_with_heading(self):
        return self.command_response('toast', heading='Information',
                                     text='toast message', position='bottom-right', icon='info')

    def button_toast_stacked(self):

        for x in range(1, 6):
            self.add_command('toast', heading='Information', text=f'toast message {x}',
                             position='bottom-right', stack=10)

        return self.command_response()

    def button_toast_sticky(self):
        return self.command_response('toast', heading='Information',
                                     text='toast message', position='bottom-right', icon='info',
                                     hideAfter=False)

    def button_toast_sticky_only_one(self):
        return self.command_response('if_not_selector', selector='#my_toast_message:visible',
                                     commands=[ajax_command('toast',
                                                            id='my_toast_message',
                                                            heading='Information',
                                                            text='Only one of me',
                                                            position='bottom-right',
                                                            icon='info',
                                                            hideAfter=False)])


class DownloadExamples(AjaxHelpers, MainMenu):
    template_name = 'ajax_examples/file_downloads.html'

    @staticmethod
    def create_excel_file():
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['hello', 'world'])
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return output

    def button_redirect_download(self, download=None):
        return self.command_response('redirect', url=reverse('download_examples') + f'?download={download}')

    @staticmethod
    def button_download_text():
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="text.txt"'
        response.write('text file data')
        return response

    def button_download_blob(self):
        filename = 'test.xlsx'
        excel_file = self.create_excel_file()
        response = HttpResponse(content_type='application/ms-excel')
        # Providing extra download information for the user's browser.
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        response.write(excel_file.read())
        return response

    def button_download_base64(self, **kwargs):
        excel_file = self.create_excel_file()
        filename = 'test_base64.xlsx'
        return self.command_response('save_file', data=base64.b64encode(excel_file.read()).decode('ascii'),
                                     filename=filename)

    def button_download_pdf(self):
        f = open('/app/sample.pdf', 'rb')
        return self.command_response('save_file', data=base64.b64encode(f.read()).decode('ascii'),
                                     filename='sample.pdf', type='application/pdf')

    def get(self, request, *args, **kwargs):
        download = request.GET.get('download')
        if download in ['1', '2']:
            download_type = 'attachment' if download == '1' else 'inline'
            f = open('/app/sample.pdf', 'rb')
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f"{download_type}; filename=test.pdf"
            response.write(f.read())
            f.close()
            return response
        return super().get(request, *args, **kwargs)


class DragDropUpload(AjaxFileUploadMixin, AjaxHelpers, MainMenu):

    template_name = 'ajax_examples/dragdrop_upload.html'

    @staticmethod
    def upload_files(filename, _size, file, **kwargs):
        path = '/media/' + filename
        with open(path, 'wb+') as destination:
            destination.write(file.read())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['files'] = os.listdir('/media/')
        return context


class EventExample(ReceiveForm, AjaxHelpers, MainMenu):

    template_name = 'ajax_examples/event.html'

    def form_test_form(self, **kwargs):

        if kwargs.get('from_event') == 'keyup':
            response = ('<span class="text-danger">Not enough chars<span>' if len(kwargs['text_entry']) < 6
                        else '<span class="text-success">All good now<span>')
            return self.command_response('html', selector='#message', html=response)

    def get_context_data(self, **kwargs):
        self.add_page_command('on', event='keyup', selector='input', commands=[
            ajax_command('send_form', form_id='test_form', from_event='keyup')
        ])
        context = super().get_context_data(**kwargs)
        context['form'] = TestForm()
        return context


class Help(AjaxHelpers, MainMenu):
    template_name = 'ajax_examples/help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['commands'] = {
            'ajax_post': 'data, (url)',
            'append_to': 'selector, html',
            'delay': 'time',
            'element_count': 'selector, data, (url)',
            'get_attr': 'selector, attr, data, (url)',
            'html': 'selector, (parent), html',
            'message': 'text',
            'console_log': 'text',
            'null': '',
            'on': 'selector, event, commands',
            'onload': 'commands',
            'reload': '',
            'redirect': 'url',
            'save_file': 'filename, data',
            'send_form': 'form_id',
            'set_attr': 'selector, attr, val',
            'set_css': 'selector, prop, val',
            'set_prop': 'selector, prop, val',
            'set_value': 'selector, val',
            'timeout': 'commands, time',
            'timer': 'commands, interval',
            'upload_file': '',
            'if_selector': 'selector, commands',
            'if_not_selector': 'selector, commands',
        }
        return context
