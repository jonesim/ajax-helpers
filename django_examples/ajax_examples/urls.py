from django.urls import path
import ajax_examples.views as views
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='ajax_main', )),
    path('ajax-redirect/', RedirectView.as_view(pattern_name='ajax_main', ), name='django-ajax-helpers'),
    path('ajax_example', views.Example1.as_view(), name='ajax_main'),
    path('redirect', views.Example2.as_view(), name='redirect'),
    path('tooltip/', views.ToolTip.as_view(), name='demo_tooltip'),
    path('timer/', views.TimerExample.as_view(), name='timer_examples'),
    path('download/', views.DownloadExamples.as_view(), name='download_examples'),
    path('dragdrop-upload/', views.DragDropUpload.as_view(), name='dragdrop_upload'),
]
