import json
from asgiref.sync import async_to_sync
from ajax_helpers.utils import ajax_command
from django.core.serializers.json import DjangoJSONEncoder
try:
    from channels.generic.websocket import WebsocketConsumer
except ImportError:
    # django channels required
    pass


class ConsumerHelper(WebsocketConsumer):
    ajax_commands = ['button', 'tooltip', 'timer', 'ajax']

    def __init__(self, *args, **kwargs):
        self.slug = {}
        super().__init__(args, kwargs)
        self.group_name = None
        self.command_set = set()
        self.response_commands = []

    def add_command(self, function_name, **kwargs):
        if type(function_name) == list:
            self.response_commands += function_name
        else:
            self.response_commands.append(ajax_command(function_name, **kwargs))

    def command_response(self, function_name=None, **kwargs):
        if function_name is not None:
            self.add_command(function_name, **kwargs)
        return json.dumps({'commands': self.response_commands}, cls=DjangoJSONEncoder)

    def split_slug(self, slug):
        if slug is not None and slug != '-':
            s = slug.split('-')
            if len(s) == 1:
                self.slug['gn'] = s[0]
            else:
                self.slug.update({s[k]: s[k+1] for k in range(0, int(len(s)-1), 2)})
            if 'gn' in self.slug:
                self.group_name = self.slug['gn']

    def connect_commands(self):
        pass
        # self.add_command('message', text='Hello world')

    def pre_connect(self):
        pass  # you can modify the channel name here

    def connect(self):
        self.split_slug(self.scope['url_route']['kwargs'].get('slug'))
        # connection has to be accepted
        self.accept()
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )
        self.connect_commands()
        self.send(self.command_response())

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

    def receive(self, text_data=None, bytes_data=None):
        pass

    def send_commands(self, event):
        self.send(text_data=json.dumps(event))
