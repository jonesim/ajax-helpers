from asgiref.sync import async_to_sync

from ajax_helpers.utils import ajax_command
try:
    from celery import Task
    from channels.layers import get_channel_layer
except ImportError:
    # django channels required / celery required
    pass


class TaskHelper(Task):

    def run(self, *args, **kwargs):
        pass

    def __init__(self, *args, **kwargs):
        self.ws_response_commands = {}
        self.channel_names = {}
        super().__init__(*args, **kwargs)

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
