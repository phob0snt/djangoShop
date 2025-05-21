from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from catalog.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalog.urls')),
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
