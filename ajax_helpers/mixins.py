import io
import csv
import json
import codecs
import inspect
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import ensure_csrf_cookie

from ajax_helpers.utils import ajax_command, is_ajax


def ajax_method(func):
    def method(*args, _ajax=True, **kwargs):
        return func(*args, **kwargs)
    return method


@method_decorator(ensure_csrf_cookie, name='dispatch')
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
        if is_ajax(request):
            if request.content_type == 'application/json':
                response = json.loads(request.body)
            elif request.content_type == 'multipart/form-data':
                response = request.POST.dict()
            else:
                response = None
            if response:
                if 'ajax_method' in response:
                    method = getattr(self, response.pop('ajax_method'))
                    if '_ajax' in inspect.signature(method).parameters:
                        return method(**response)
                    else:
                        raise Exception(f'Method {method.__qualname__} is not enabled for ajax. '
                                        f'Use decorator ajax_method.')
                else:
                    for t in self.command_set:
                        if t in response and hasattr(self, f'{t}_{response[t]}'):
                            method = getattr(self, f'{t}_{response[t]}')
                            del response[t]
                            return method(**response)
        if hasattr(super(), 'post'):
            # noinspection PyUnresolvedReferences
            return super().post(request, *args, **kwargs)

    def add_page_command(self, function_name, **kwargs):
        if type(function_name) == list:
            self.page_commands += function_name
        else:
            self.page_commands.append(ajax_command(function_name, **kwargs))

    def get_page_commands(self):
        return []

    def get_context_data(self, **kwargs):
        # noinspection PyUnresolvedReferences
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        self.page_commands += self.get_page_commands()
        if self.page_commands:
            command = ajax_command('onload', commands=self.page_commands)
            context['ajax_helpers_script'] = mark_safe(
                f'<script>ajax_helpers.process_commands([{json.dumps(command)}])</script>'
            )
        return context

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ReceiveForm:

    def post(self, request, *args, **kwargs):
        if is_ajax(request) and request.content_type == 'multipart/form-data':
            if 'form_id' in request.POST:
                return getattr(self, f'form_{request.POST["form_id"]}')(**request.POST.dict())
        # noinspection PyUnresolvedReferences
        return super().post(request, *args, **kwargs)


class UTF8EncodedStringIO(io.StringIO):
    def next(self):
        # noinspection PyUnresolvedReferences
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

    # noinspection PyUnusedLocal
    @staticmethod
    def file_upload(file):
        return JsonResponse({'file': 'ok'})

    def post(self, request, *args, **kwargs):
        if is_ajax(request) and request.content_type == 'multipart/form-data' and 'ajax_file' in request.FILES:
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

    # noinspection PyUnresolvedReferences
    def post(self, request, *args, **kwargs):
        if is_ajax(request) and request.content_type == 'multipart/form-data' and self.upload_key in request.FILES:
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
        # noinspection PyUnresolvedReferences
        return self.command_response('upload_file', **self.upload_file_command(0, **kwargs))

    # noinspection PyUnresolvedReferences
    def upload_completed(self):
        self.add_command('delay', time=500)
        self.add_command('message', text='Upload complete')
        return self.command_response('reload')


class AjaxTaskMixin:
    refresh_ms = 600
    tasks = {}

    def task_progress(self, info):
        pass

    # noinspection PyUnusedLocal, PyUnresolvedReferences
    def task_state_success(self, task_result, task_name, **kwargs):
        return self.command_response('null')

    # noinspection PyUnusedLocal, PyUnresolvedReferences
    def task_state_failure(self, task_result, task_name, **kwargs):
        return self.command_response('null')

    # noinspection PyUnusedLocal, PyUnresolvedReferences
    def task_state_revoked(self, _task_result, task_name, **kwargs):
        return self.command_response('null')

    def ajax_check_result(self, *, task_id, task_name, **kwargs):
        task_result = self.tasks[task_name].AsyncResult(task_id)
        state_method = getattr(self, 'task_state_' + task_result.state.lower(), None)
        if state_method:
            return state_method(task_result=task_result, task_name=task_name, **kwargs)
        if isinstance(task_result.info, dict):
            self.task_progress(task_result.info)
        # noinspection PyUnresolvedReferences
        return self.command_response(
            'timeout', time=self.refresh_ms, commands=[ajax_command('ajax_post', url=self.request.path, data=dict(
                ajax='check_result', task_id=task_result.id, task_name=task_name, **kwargs
            ))]
        )

    def start_task(self, task_name, task_kwargs=None, result_kwargs=None):
        if not task_kwargs:
            task_kwargs = {}
        if not result_kwargs:
            result_kwargs = {}
        task = self.tasks[task_name].delay(**task_kwargs)
        return self.ajax_check_result(task_id=task.id, task_name=task_name, **result_kwargs)
