from django.urls import path, include
from . import views

urlpatterns = [    
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user_home/',views.user_home,name='user_home'),
    path('manager_dashboard/',views.manager_dashboard,name='manager_dashboard'),
    path('user_activity/',views.user_activity,name='user_activity'),
    path('add_an_event/',views.add_an_event,name='add_an_event'),
    path('manage_spacific_event/',views.manage_spacific_event,name='manage_spacific_event'),
]

