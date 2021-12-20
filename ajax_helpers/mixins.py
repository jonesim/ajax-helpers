import io
import csv
import json
import codecs
import inspect
from django.http import JsonResponse
from django.utils.safestring import mark_safe

from ajax_helpers.utils import ajax_command


class AjaxHelpers:
    ajax_commands = ['button', 'tooltip', 'timer', 'ajax']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_set = set()
        for c in inspect.getmro(self.__class__):
            self.command_set = self.command_set | set(getattr(c, 'ajax_commands', []))
        self.response_commands = []
        self.page_commands = []

    def add_command(self, function_name, **kwargs):
        if type(function_name) == list:
            self.response_commands += function_name
        else:
            self.response_commands.append(ajax_command(function_name, **kwargs))

    def command_response(self, function_name=None, **kwargs):
        if function_name is not None:
            self.add_command(function_name, **kwargs)
        return JsonResponse(self.response_commands, safe=False)

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            if request.content_type == 'application/json':
                response = json.loads(request.body)
            elif request.content_type == 'multipart/form-data':
                response = request.POST.dict()
            else:
                response = None
            if response:
                for t in self.command_set:
                    if t in response and hasattr(self, f'{t}_{response[t]}'):
                        method = getattr(self, f'{t}_{response[t]}')
                        del response[t]
                        return method(**response)
        if hasattr(super(), 'post'):
            return super().post(request, *args, **kwargs)

    def add_page_command(self, function_name, **kwargs):
        if type(function_name) == list:
            self.page_commands += function_name
        else:
            self.page_commands.append(ajax_command(function_name, **kwargs))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        if self.page_commands:
            command = ajax_command('onload', commands=self.page_commands)
            context['ajax_helpers_script'] = mark_safe(
                f'<script>ajax_helpers.process_commands([{json.dumps(command)}])</script>'
            )
        return context


class ReceiveForm:

    def post(self, request, *args, **kwargs):
        if request.is_ajax() and request.content_type == 'multipart/form-data':
            if 'form_id' in request.POST:
                return getattr(self, f'form_{request.POST["form_id"]}')(**request.POST.dict())
        return super().post(request, *args, **kwargs)


class UTF8EncodedStringIO(io.StringIO):
    def next(self):
        return super(UTF8EncodedStringIO, self).next().encode('utf-8')


class AjaxFileHelpers(AjaxHelpers):

    @staticmethod
    def get_csv(file):
        s = file.read()
        if s.startswith(codecs.BOM_UTF8):
            s = s[3:]
        s = s.decode('latin1')
        stream = UTF8EncodedStringIO(s)
        return csv.DictReader(stream, delimiter=',')

    @staticmethod
    def file_upload(file):
        return JsonResponse({'file': 'ok'})

    def post(self, request, *args, **kwargs):
        if request.is_ajax() and request.content_type == 'multipart/form-data' and 'ajax_file' in request.FILES:
            return self.file_upload(request.FILES['ajax_file'])
        return super().post(request, *args, **kwargs)


class AjaxFileUploadMixin:
    ajax_commands = ['start_upload', 'upload']
    upload_key = 'ajax_modal_file'
    single_progress_bar = True

    def progress_bar_id(self, index):
        if self.single_progress_bar:
            index = 0
        return f'#file_progress_bar_{index}'

    def post(self, request, *args, **kwargs):
        if request.is_ajax() and request.content_type == 'multipart/form-data' and self.upload_key in request.FILES:
            response = request.POST.dict()
            file = self.request.FILES[self.upload_key]
            upload_params = json.loads(response.get('upload_params', '{}'))
            index = int(response.pop('index'))
            file_info = [f for f in json.loads(response['file_info']) if f['size'] > 0]
            getattr(self, 'upload_' + request.POST['upload'])(file_info[index]['name'], file_info[index]['size'], file,
                                                              **upload_params)
            if len(file_info) > index + 1:
                response['upload_params'] = upload_params
                return self.command_response('upload_file', **self.upload_file_command(index + 1, **response))
            return self.upload_completed()
        return super().post(request, *args, **kwargs)

    def upload_file_command(self, index, **kwargs):
        upload_file = {k: v for k, v in kwargs.items() if k in ['upload_params', 'drag_drop', 'selector']}
        upload_file.update({'options': {'progress': {'selector': self.progress_bar_id(index)}}, 'index': index})
        return upload_file

    def start_upload_files(self, **kwargs):
        kwargs['files'] = [f for f in kwargs['files'] if f['size'] > 0]
        if len(kwargs['files']) == 0:
            return self.upload_completed()
        return self.command_response('upload_file', **self.upload_file_command(0, **kwargs))

    def upload_completed(self):
        self.add_command('delay', time=500)
        self.add_command('message', text='Download complete')
        return self.command_response('reload')
