from django.urls import path
from . import views

urlpatterns = [
    path('chart/', views.forecast_chart, name='forecast_chart'),
]