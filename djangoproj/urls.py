from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from App import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('App.urls')),
    
    # Serve static files directly
    re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT,
        'show_indexes': True,
    }),
    
    # Serve media files
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
        'show_indexes': True,
    }),
    
    # Serve favicon and logo directly from static files
    path('favicon.ico', serve, {
        'path': 'favicon.ico',
        'document_root': settings.STATIC_ROOT,
    }),
    path('logo192.png', serve, {
        'path': 'logo192.png',
        'document_root': settings.STATIC_ROOT,
    }),
    
    # Catch-all for React routes
    re_path(r'^.*$', views.index, name='index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)