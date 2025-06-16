from django.urls import path
from . import views

app_name = 'blockchainproject'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('get-balance/', views.get_balance, name='get_balance'),
    path('transfer/', views.transfer, name='transfer'),
]