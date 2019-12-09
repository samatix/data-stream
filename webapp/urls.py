from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from generic.views import index
from generic.api_urls import router as data_router
from . import routers


"""
URL definitions for the api.
"""
router = routers.DefaultRouter()
router.extend(data_router)

urlpatterns = [
    path('', index),
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name="login"),
    path('accounts/logout/', LogoutView.as_view(template_name='registration/logged_out.html'), name="logout"),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]