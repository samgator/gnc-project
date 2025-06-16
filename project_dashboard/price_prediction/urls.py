from django.urls import path
from . import views

app_name = 'price_prediction'

urlpatterns = [
    path('', views.index, name='index'),
    path('get-prediction-data/', views.get_prediction_data, name='get_prediction_data'),
] 