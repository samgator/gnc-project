from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', index, name='homepage'),  # You may want to update this to your new homepage view
    # path('manage/', manage, name='manage'),  # Update or remove as needed
    # path('forecast/', include('forecast.urls')),  # Removed forecast app
    path('blockchain/', include('blockchainproject.urls')),
] 