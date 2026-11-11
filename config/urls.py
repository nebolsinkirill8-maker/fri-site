from django.contrib import admin
from django.urls import include, path

urlpatterns = [path('admin/', admin.site.urls), path('support/', include('support.urls')), path('', include('portal.urls'))]
