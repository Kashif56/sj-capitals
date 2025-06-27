from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('contact-us/', views.contact_us, name='contact'),
    path('payment/<int:plan_id>/', views.payment, name='payment'),
]