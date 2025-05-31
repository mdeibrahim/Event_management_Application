from django.urls import path
from . import views

urlpatterns = [
    path('', views.public_home, name='public_home'),
    path('sign_in/', views.sign_in, name='sign_in'),
    path('sign_up/', views.sign_up, name='sign_up'),
]