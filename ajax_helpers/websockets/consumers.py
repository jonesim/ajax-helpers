import json
from asgiref.sync import async_to_sync
from ajax_helpers.utils import ajax_command
from django.core.serializers.json import DjangoJSONEncoder
try:
    from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
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


class AsyncConsumerHelper(AsyncWebsocketConsumer):
    """Async equivalent of ConsumerHelper, with an identical wire protocol.

    Same {"commands": [...]} payload and the same 'send.commands' group event, so
    group_send callers and the client JS need no changes -- only the base class differs.

    Why you may want it
    -------------------
    ConsumerHelper is a synchronous WebsocketConsumer. Channels dispatches sync consumers
    through @database_sync_to_async, and Channels does not open an asgiref
    ThreadSensitiveContext anywhere, so every dispatch falls through to
    SyncToAsync.single_thread_executor -- a class-level, process-wide
    ThreadPoolExecutor(max_workers=1). Every connect, disconnect and group handler for every
    socket in the whole process therefore runs one at a time on one thread. Django's HTTP path
    opens a context of its own, so requests are unaffected; only websockets are pinched. On a
    consumer every page subscribes to, and with a group_send fanning out to many sockets, that
    queue is the bottleneck.

    Nothing in this helper needs a thread: group_add, group_discard and send are natively
    async, and the sync version only wraps them in async_to_sync to fit its base class.

    What this does NOT do
    ---------------------
    It does not take the consumer off that thread. Channels awaits aclose_old_connections()
    before every handler and again in websocket_disconnect, and that is
    sync_to_async(close_old_connections) -- thread_sensitive, so the same executor. Measured
    transits per socket lifecycle, instrumenting single_thread_executor.submit against a real
    redis channel layer:

        ConsumerHelper       connect=1  broadcast=1  disconnect=1   total 3
        AsyncConsumerHelper  connect=1  broadcast=1  disconnect=2   total 4

    The count is one higher. What changes is what each transit holds: the whole handler
    including the redis round-trip on the sync path, versus close_old_connections() here,
    which is microseconds and touches no network. So this shortens the hop rather than
    removing it -- a stuck job on that thread still blocks websockets either way.
    AuthMiddlewareStack, if used, also puts a get_user read on it per connect.

    Subclassing
    -----------
    connect_commands and pre_connect are coroutines here, and both are awaited. A subclass that
    overrides one with a plain def does NOT fail quietly: the body runs synchronously on the
    event loop and then `await None` raises TypeError inside connect(). For pre_connect that is
    before accept(), so the handshake never completes and the client's reconnect loop retries
    every couple of seconds indefinitely; for connect_commands it is after accept(), so the
    socket opens and immediately dies without its first frame. Convert overrides when switching.

    Anything touching the ORM in them needs database_sync_to_async. And note that blocking code
    in an async consumer blocks the event loop -- every socket and, under Daphne, every HTTP
    request -- rather than one thread.

    Unlike ConsumerHelper, this actually calls pre_connect(); the sync class defines the hook
    but never invokes it. The two combine badly for anyone migrating a subclass: a pre_connect
    that has never once run under the sync class starts running here, and if it was left as a
    plain def it takes the handshake down with it.
    """

    ajax_commands = ['button', 'tooltip', 'timer', 'ajax']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        # Kept equivalent to ConsumerHelper.split_slug so existing slugs parse identically.
        if slug is not None and slug != '-':
            s = slug.split('-')
            if len(s) == 1:
                self.slug['gn'] = s[0]
            else:
                self.slug.update({s[k]: s[k + 1] for k in range(0, int(len(s) - 1), 2)})
            if 'gn' in self.slug:
                self.group_name = self.slug['gn']

    async def connect_commands(self):
        pass

    async def pre_connect(self):
        pass  # you can modify the channel name here

    async def connect(self):
        self.split_slug(self.scope['url_route']['kwargs'].get('slug'))
        await self.pre_connect()
        await self.accept()
        # A slug of '-' (or one with no gn key) leaves group_name None, and channels_redis
        # rejects a None group. The sync class adds unconditionally and so dies in the
        # handshake; a socket with no group simply receives no broadcasts.
        if self.group_name:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.connect_commands()
        await self.send(text_data=self.command_response())

    async def disconnect(self, close_code):
        # Mirrors the guard in connect: nothing joined, nothing to discard.
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def send_commands(self, event):
        # The whole event dict is forwarded, 'type' included, exactly as the sync helper does.
        await self.send(text_data=json.dumps(event))
