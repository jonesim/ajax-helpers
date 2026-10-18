import json
from asgiref.sync import async_to_sync
from ajax_helpers.utils import ajax_command
from django.core.serializers.json import DjangoJSONEncoder
try:
    from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
except ImportError:
    # django channels required
    pass


class ConsumerHelperMixin:
    """Command building and slug parsing shared by the sync and async helpers."""

    ajax_commands = ['button', 'tooltip', 'timer', 'ajax']

    def _init_helper_state(self):
        self.slug = {}
        self.group_name = None
        self.command_set = set()
        self.response_commands = []

    def add_command(self, function_name, **kwargs):
        if isinstance(function_name, list):
            self.response_commands += function_name
        else:
            self.response_commands.append(ajax_command(function_name, **kwargs))

    def command_response(self, function_name=None, **kwargs):
        if function_name is not None:
            self.add_command(function_name, **kwargs)
        return json.dumps({'commands': self.response_commands}, cls=DjangoJSONEncoder)

    def split_slug(self, slug):
        if slug is not None and slug != '-':
            parts = slug.split('-')
            if len(parts) == 1:
                self.slug['gn'] = parts[0]
            else:
                self.slug.update({parts[k]: parts[k + 1] for k in range(0, len(parts) - 1, 2)})
            if 'gn' in self.slug:
                self.group_name = self.slug['gn']


class ConsumerHelper(ConsumerHelperMixin, WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        self._init_helper_state()
        super().__init__(args, kwargs)

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


class AsyncConsumerHelper(ConsumerHelperMixin, AsyncWebsocketConsumer):
    """Async version of ConsumerHelper with the same wire protocol.

    Channels runs every sync consumer in a process on one shared thread; this one runs on the event loop.
    connect_commands and pre_connect are coroutines, so overrides must be async def (a plain def raises TypeError
    in connect), and ORM access needs database_sync_to_async. Unlike ConsumerHelper, pre_connect is called.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_helper_state()

    async def connect_commands(self):
        pass

    async def pre_connect(self):
        pass  # you can modify the channel name here

    async def connect(self):
        self.split_slug(self.scope['url_route']['kwargs'].get('slug'))
        await self.pre_connect()
        await self.accept()
        # No gn in the slug leaves group_name None, which channels_redis rejects
        if self.group_name:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.connect_commands()
        await self.send(text_data=self.command_response())

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def send_commands(self, event):
        await self.send(text_data=json.dumps(event))
