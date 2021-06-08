from django.urls import path
import examples.views as views


urlpatterns = [
    path('', views.Example1.as_view()),
    path('redirect', views.Example2.as_view(), name='redirect'),
    path('tooltip/', views.ToolTip.as_view(), name='demo_tooltip')
]
