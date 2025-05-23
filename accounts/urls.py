from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
]