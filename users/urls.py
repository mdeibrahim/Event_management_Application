from django.urls import path, include
from . import views

urlpatterns = [    
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user_home/',views.user_home,name='user_home'),
    path('manager_dashboard/',views.manager_dashboard,name='manager_dashboard'),
    path('user_activity/',views.user_activity,name='user_activity'),
    path('add_an_event/',views.add_an_event,name='add_an_event'),
    path('manage_spacific_event/<uuid:event_id>/',views.manage_spacific_event,name='manage_spacific_event'),
    path('manager_update_event/<uuid:event_id>/',views.manager_update_event,name='manager_update_event'),
    path('manager_delete_event/<uuid:event_id>/',views.manager_delete_event,name='manager_delete_event'),
    path('accept_request/<int:request_id>/', views.accept_request, name='accept_request_url'),
    path('reject_request/<int:request_id>/', views.reject_request, name='reject_request_url'),
    path('invite_user/<uuid:event_id>/', views.invite_user, name='invite_user'),
    path('join_event/<uuid:event_id>/', views.join_event, name='join_event'),
    path('accept_invitation/<uuid:event_id>/', views.accept_invitation, name='accept_invitation'),
    path('decline_invitation/<uuid:event_id>/', views.decline_invitation, name='decline_invitation'),
]

