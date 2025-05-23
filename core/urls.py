from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('payment/<int:plan_id>/', views.payment, name='payment'),
]