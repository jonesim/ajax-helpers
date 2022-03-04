from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from asgiref.sync import async_to_sync
from ajax_helpers.utils import ajax_command
try:
    from channels.layers import get_channel_layer
except ImportError:
    # django channels required
    pass


class WebsocketHelpers:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_response_commands = {}
        self.channel_names = {}

    def add_ws_command(self, channel_name, function_name, **kwargs):
        if channel_name not in self.ws_response_commands:
            self.ws_response_commands[channel_name] = []
        if type(function_name) == list:
            self.ws_response_commands[channel_name] += function_name
        else:
            self.ws_response_commands[channel_name].append(ajax_command(function_name, **kwargs))

    def send_ws_commands(self, channel_name, function_name=None, **kwargs):
        if function_name is not None:
            self.add_ws_command(channel_name, function_name, **kwargs)

        commands = self.ws_response_commands.get(channel_name, [])
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(channel_name, {"type": "send.commands", 'commands': commands})

    def add_channel(self, channel_name, ws_url=None):
        if ws_url is None:
            ws_url = '/helpers'
        url = f'{ws_url}/gn-{channel_name}/'
        self.channel_names[channel_name] = url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}

        if self.channel_names:
            websocket_helpers_scripts = ''
            for channel_name, ws_url in self.channel_names.items():
                websocket_helpers_scripts += render_to_string('ajax_helpers/websocket_helpers_script.html',
                                                              {'channel_name': channel_name,
                                                               'ws_url': ws_url})
            context['websocket_helpers_scripts'] = mark_safe(websocket_helpers_scripts)
        return context
