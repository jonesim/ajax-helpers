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

from ajax_helpers.mixins import AjaxHelpers, ReceiveForm, AjaxFileHelpers, AjaxFileUploadMixin
from ajax_helpers.utils import ajax_command


class MainMenu(DemoViewMixin, MenuMixin):

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('main_menu').add_items(
            ('ajax_main', 'General'),
            ('timer_examples', 'Timers'),
            ('download_examples', 'File Downloads'),
            ('dragdrop_upload', 'File Uploads'),
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


class Example1(MainMenu, AjaxFileHelpers, ReceiveForm, AjaxHelpers, TemplateView):

    template_name = 'ajax_examples/main.html'

    def button_redirect(self):
        self.add_command('message', text='Will redirect after this message')
        self.add_command('redirect', url=reverse('redirect'))
        return self.command_response()

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
        self.add_command('append_to', html='<div>New div</div>', element='#append-to')
        return self.command_response()

    def button_css(self):
        self.add_command('set_css', selector='#css-test', prop='width', val='800px')
        return self.command_response('set_css', selector='#css-test', prop='background-color', val='yellow')

    def button_null(self):
        return self.command_response('null')

    def file_upload(self, file):
        return self.command_response('message', text=f'Received {file.name} size {file.size}')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TestForm()
        return context

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'filter': filter}


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
            'timer', commands=[ajax_command('ajax_post', url=self.request.path, data={'timer': 'test'})], interval=2000
        )

        return super().get_context_data(**kwargs)


class DownloadExamples(Example1):
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


class DragDropUpload(AjaxFileUploadMixin, Example1):

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
