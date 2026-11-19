from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from .applications import application
from .forms import EmailAuthenticationForm

urlpatterns = [
    path('accounts/profile/photo/', views.profile_photo, name='profile_photo'),
    path('', views.home, name='home'),
    path('tournament/', views.tournament, name='tournament'),
    path('zxc/', views.zxc, name='zxc'),
    path('privacy/', views.privacy, name='privacy'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html', authentication_form=EmailAuthenticationForm, redirect_authenticated_user=True), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/profile/edit/', views.profile_edit, name='profile_edit'),
    path('accounts/application/', application, name='application'),
    path('accounts/zxc-application/', application, {'competition': 'zxc'}, name='zxc_application'),
]
