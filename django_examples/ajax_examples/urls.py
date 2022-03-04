from django.urls import path
import ajax_examples.views as views
from django.views.generic import RedirectView

from ajax_helpers.screen_capture import ChooseAudioModal

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='ajax_main', )),
    path('ajax-redirect/', RedirectView.as_view(pattern_name='ajax_main', ), name='django-ajax-helpers'),
    path('ajax_example', views.Example1.as_view(), name='ajax_main'),
    path('redirect', views.Example2.as_view(), name='redirect'),
    path('tooltip/', views.ToolTip.as_view(), name='demo_tooltip'),
    path('timer/', views.TimerExample.as_view(), name='timer_examples'),
    path('toast/', views.ToastExample.as_view(), name='toast_examples'),
    path('download/', views.DownloadExamples.as_view(), name='download_examples'),
    path('dragdrop-upload/', views.DragDropUpload.as_view(), name='dragdrop_upload'),
    path('event/', views.EventExample.as_view(), name='event_example'),
    path('help/', views.Help.as_view(), name='help'),
    path('choose-audio/<str:base64>/', ChooseAudioModal.as_view(), name='choose_audio_modal'),
]
