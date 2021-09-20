from django.urls import path
import ajax_examples.views as views
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='ajax_main', )),
    path('ajax_example', views.Example1.as_view(), name='ajax_main'),
    path('redirect', views.Example2.as_view(), name='redirect'),
    path('tooltip/', views.ToolTip.as_view(), name='demo_tooltip')
]
