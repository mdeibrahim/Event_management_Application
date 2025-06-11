
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    # path('tasks/', include('tasks.urls')),
    path('users/', include('users.urls')),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path("__reload__/", include("django_browser_reload.urls")),  # Re-enabled for auto-reloading
    # path('__debug__/', include('debug_toolbar.urls')),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
