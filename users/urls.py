from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns = [    
    # path('admin_home/', views.admin_home, name='admin_home'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/groups/', views.admin_groups, name='admin_groups'),
    path('admin/permissions/', views.admin_permissions, name='admin_permissions'),
    path('admin/events/', views.admin_events, name='admin_events'),
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin/registrations/', views.admin_registrations, name='admin_registrations'),
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/profiles/', views.admin_profiles, name='admin_profiles'),
    # path('admin/user/edit/<int:user_id>/', views.admin_edit_user, name='admin_user_edit'),
    path('admin/edit-user/<int:user_id>/', views.admin_edit_user, name='admin_user_edit'),

    path('admin/password-reset/<int:user_id>/', views.AdminUserPasswordResetView.as_view(), name='admin_password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='admin/password_reset_confirm.html',success_url=reverse_lazy('login')),name='password_reset_confirm'),
    # path('admin/reset-password/<int:user_id>/', views.admin_reset_password, name='admin_reset_password'),
   
    # 2. convert FBV to CBV path('user_home/',views.user_home,name='user_home'),
    path('user_home/',views.UserHomeView.as_view(),name='user_home'),
    # 1. convert FBV to CBV path('manager_dashboard/',views.manager_dashboard,name='manager_dashboard'),
    path('manager_dashboard/',views.ManagerDashboardView.as_view(),name='manager_dashboard'),
    # 3. convert FBV to CBV path('user_activity/',views.user_activity,name='user_activity'),
    path('user_activity/',views.UserActivityView.as_view(),name='user_activity'),
    path('add_an_event/',views.add_an_event,name='add_an_event'),
    # 4. convert FBV to CBV path('manage_spacific_event/<uuid:event_id>/',views.manage_spacific_event,name='manage_spacific_event'),
    path('manage_spacific_event/<uuid:event_id>/',views.ManageSpacificEventView.as_view(),name='manage_spacific_event'),
    # 5. convert FBV to CBV path('manager_update_event/<uuid:event_id>/',views.manager_update_event,name='manager_update_event'),
    path('manager_update_event/<uuid:event_id>/',views.ManagerUpdateEventView.as_view(),name='manager_update_event'),
    path('manager_delete_event/<uuid:event_id>/',views.manager_delete_event,name='manager_delete_event'),
    path('accept_request/<int:request_id>/', views.accept_request, name='accept_request_url'),
    path('reject_request/<int:request_id>/', views.reject_request, name='reject_request_url'),
    path('invite_user/<uuid:event_id>/', views.invite_user, name='invite_user'),
    path('join_event/<uuid:event_id>/', views.join_event, name='join_event'),
    path('accept_invitation/<uuid:event_id>/', views.accept_invitation, name='accept_invitation'),
    path('decline_invitation/<uuid:event_id>/', views.decline_invitation, name='decline_invitation'),
    path('user_profile/',views.user_profile,name='user_profile'),
    path('have_a_fun',views.have_a_fun,name='have_a_fun'),
    path('admin/test-email/', views.test_email, name='test_email'),
    
    path('update-profile',views.UpdateProfileView.as_view(),name='update_profile'),
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    
    path('password-reset/',auth_views.PasswordResetView.as_view(),name='password_reset'),
    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(),name='password_reset_confirm'),
    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

