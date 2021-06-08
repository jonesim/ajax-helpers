import io
import csv
import json
import codecs
from django.http import JsonResponse


class AjaxHelpers:
    ajax_commands = ['button', 'tooltip', 'timer']

    def __init__(self):
        super().__init__()
        self.response_commands = []

    def add_command(self, function_name, **kwargs):
        kwargs['function'] = function_name
        self.response_commands.append(kwargs)

    def command_response(self, function_name=None, **kwargs):
        if function_name is not None:
            self.add_command(function_name, **kwargs)
        return JsonResponse(self.response_commands, safe=False)

    def post(self, request, *args, **kwargs):
        if request.is_ajax() and request.content_type == 'application/json':
            response = json.loads(request.body)
            for t in self.ajax_commands:
                if t in response:
                    return getattr(self, f'{t}_{response[t]}')(**response)
        return super().post(request, *args, **kwargs)


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