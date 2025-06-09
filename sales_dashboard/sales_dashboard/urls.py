from django.contrib import admin
from django.urls import path, include
from forecast.views import homepage

urlpatterns = [
    path("admin/", admin.site.urls),
    path('',  homepage, name='homepage'),
    path('forecast/', include('forecast.urls')),
]
