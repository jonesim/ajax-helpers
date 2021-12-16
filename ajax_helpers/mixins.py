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
            self.command_set = self.command_set | set(getattr(c,'ajax_commands', []))
        self.response_commands = []

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
                response = request.POST
            else:
                response = None
            if response:
                for t in self.command_set:
                    if t in response and hasattr(self, f'{t}_{response[t]}'):
                        return getattr(self, f'{t}_{response[t]}')(**response)
        if hasattr(super(), 'post'):
            return super().post(request, *args, **kwargs)

    def get_ajax_onload(self):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        onload = self.get_ajax_onload()
        if onload:
            command = ajax_command('onload', commands=[onload])
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
