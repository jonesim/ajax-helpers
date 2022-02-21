import json
from django.forms.fields import ChoiceField
from django.template.loader import render_to_string
from django.urls import reverse
from django_menus.menu import MenuItem, HtmlMenu
from django_modals.forms import CrispyForm
from django_modals.modals import FormModal


class MenuItemAjax(MenuItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, link_type=MenuItem.AJAX_BUTTON, **kwargs)


class MenuItemJavascript(MenuItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, link_type=MenuItem.JAVASCRIPT, **kwargs)


class ScreenCaptureMixin:

    def button_exit_capture(self):
        return self.command_response('redirect', url=self.request.path)

    def button_capture(self, **kwargs):
        menu = self.capture_menu('record', 'far fa-circle', 'btn-success', 'record', 'mic', 'exit')
        return self.command_response('html', selector='body', html=render_to_string(
            'ajax_helpers/screen_capture.html', {'menu': menu, 'extra_data': json.dumps(kwargs)}, self.request
        ))

    @staticmethod
    def capture_dropdown(*args):
        dropdown_items = {
            'pause': MenuItemAjax('pause', 'Pause', font_awesome='fas fa-pause'),
            'exit': MenuItemAjax('exit_capture', ' Exit Capture', font_awesome='fas fa-times'),
            'record': MenuItemAjax('record', ' Start Recording', font_awesome='fas fa-circle'),
            'upload': MenuItemAjax('upload_capture', 'Upload', font_awesome='fas fa-upload'),
            'resume': MenuItemAjax('resume', 'Resume', font_awesome='fas fa-play'),
            'mic': MenuItemJavascript(
                f"screen_capture.audio_devices('{reverse('choose_audio_modal', args=('%1%',))}')",
                ' Select Mic', font_awesome='fas fa-microphone'),
        }
        return [dropdown_items[i] for i in args]

    def capture_menu(self, function, icon, css_class, *dropdown):
        return HtmlMenu(None, 'button_group').add_items(
            MenuItemAjax(function, menu_display='', font_awesome=icon, css_classes='btn btn-sm ' + css_class,
                         dropdown=(self.capture_dropdown(*dropdown)), placement='bottom-end')).render()

    def button_recording_started(self):
        return self.command_response(
            'html', selector='.record-menu',
            html=self.capture_menu('pause', 'fas fa-pause', 'btn-danger', 'pause', 'upload', 'exit')
        )

    def button_record(self):
        return self.command_response('start_capture')

    def button_pause(self):
        self.add_command('html', selector='.record-menu',
                         html=self.capture_menu('resume', 'fas fa-play', 'btn-warning', 'resume', 'upload', 'exit'))
        return self.command_response('pause_resume')

    def button_resume(self):
        return self.command_response('pause_resume')

    def button_upload_capture(self):
        return self.command_response('upload_capture')

    def ajax_upload_video(self, **_kwargs):
        pass


class ChooseAudio(CrispyForm):
    audio_device = ChoiceField()


class ChooseAudioModal(FormModal):
    form_class = ChooseAudio
    modal_title = 'Choose Audio input'

    def form_setup(self, form, *_args, **kwargs):
        form.fields['audio_device'].choices = self.slug['base64']

    def form_valid(self, form):
        self.add_command('set_audio_source', audio_source=form.cleaned_data['audio_device'])
        return self.command_response('close')
