from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, index
from sales.views import SaleViewSet
from .auth_views import admin_login

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

# Create router for ViewSets
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'sales', SaleViewSet, basename='sale')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', admin_login),
    path('api/', include(router.urls)),
    path('api/reporting/', include('reporting.urls')),
    path('api/todos/', include('todos.urls')),
    
    # Serve static files in development
    path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    
    # Catch-all for React routing - MUST be last
    re_path(r'^.*$', index, name='index'),
]

# Serve static files and media in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
