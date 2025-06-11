from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from tasks.models import Event, EventCategory,Profile,User, EventRegistration, Notification
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time
from django.db.models import Q,Prefetch
from .forms import InviteUserForm, ProfileUpdateForm
from django.http import JsonResponse
import logging
from django.urls import reverse, reverse_lazy
from users.forms import EventUpdateForm
from django.core.paginator import Paginator
from django.contrib.auth.models import Group,Permission
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.views import PasswordResetView, PasswordChangeView as BasePasswordChangeView
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings


logger = logging.getLogger(__name__)

User = get_user_model()

def is_event_running(event_date, event_time):
    """Helper function to check if an event is currently running"""
    current_time = timezone.now()
    current_date = current_time.date()
    current_time_only = current_time.time()
    
    return (event_date == current_date and 
            event_time and current_time_only >= event_time)

def is_admin(user):
    """Helper function to check if user is an admin"""
    return user.is_superuser

def get_filtered_events(user_events, request):
    """Helper function to filter events based on type parameter"""
    type = request.GET.get('type')
    if type == 'total':
        events_type = user_events
        event_list_title = "Total Events"
    elif type == 'upcoming':
        events_type = user_events.filter(date__gte=timezone.now().date())
        event_list_title = "Upcoming Events"
    elif type == 'past':
        events_type = user_events.filter(date__lt=timezone.now().date())
        event_list_title = "Past Events"
    else:
        events_type = user_events.filter(date=timezone.now().date())
        event_list_title = "Today's Events"
    
    return events_type, event_list_title

# Create your views here.

def have_a_fun(request):
    return render(request, 'have_a_fun.html')

# @login_required
# def admin_home(request):
#     return render(request, 'admin/admin_user_home.html')

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('have_a_fun')
    total_events=Event.objects.all()
    total_users=User.objects.all()
    # total_revenue=(total_events*5)
    context={
        'total_events':total_events.count(),
        'total_users':total_users.count(),
        'total_revenue':(total_users.count()*10)+(total_events.count()*5),
    }
    return render(request, 'admin/admin_dashboard_home.html',context)

@login_required
def admin_users(request):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('admin_dashboard')
    
    # Base queryset with all necessary related data and optimized group prefetch
    users = User.objects.select_related('profile').prefetch_related(
        Prefetch('groups', queryset=Group.objects.only('name').order_by('id'))
    )
    
    # Get filter parameters
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    action = request.GET.get('action')
    
    # Apply filters
    if role_filter:
        if role_filter == 'ADMIN':
            users = users.filter(is_superuser=True)
        elif role_filter == 'EVENT_MANAGER':
            users = users.filter(is_staff=True, is_superuser=False)
        elif role_filter == 'GENERAL_USER':
            users = users.filter(is_staff=False, is_superuser=False)
    
    if status_filter:
        users = users.filter(is_active=(status_filter == 'active'))
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Order users
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 10)
    page = request.GET.get('page')
    paginated_user = paginator.get_page(page)
    
    # Get role names for each user in the current page using prefetched groups
    for user in paginated_user:
        if user.is_superuser:
            user.role_name = 'Admin'
        elif user.is_staff:
            user.role_name = 'Event Manager'
        else:
            # Use prefetched groups instead of making a new query
            user.role_name = user.groups.first().name if user.groups.exists() else 'General User'
    
    context = {
        'users': paginated_user,
        'page_obj': paginated_user,
        'total_users': paginator.count,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'action': action,
    }
    return render(request, 'admin/users.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_groups(request):
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all groups
    groups = Group.objects.all()
    
    # Apply search filter
    if search_query:
        groups = groups.filter(name__icontains=search_query)
    
    # Order groups by name
    groups = groups.order_by('name')
    
    context = {
        'groups': groups,
        'search_query': search_query,
    }
    return render(request, 'admin/groups.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_permissions(request):
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all permissions
    permissions = Permission.objects.select_related('content_type').all()
    
    # Apply search filter
    if search_query:
        permissions = permissions.filter(
            Q(name__icontains=search_query) |
            Q(codename__icontains=search_query) |
            Q(content_type__model__icontains=search_query)
        )
    
    # Order permissions by content type and name
    permissions = permissions.order_by('content_type__app_label', 'content_type__model', 'name')
    
    # Group permissions by content type
    grouped_permissions = {}
    for permission in permissions:
        key = f"{permission.content_type.app_label}.{permission.content_type.model}"
        if key not in grouped_permissions:
            grouped_permissions[key] = {
                'content_type': permission.content_type,
                'permissions': []
            }
        grouped_permissions[key]['permissions'].append(permission)
    
    context = {
        'grouped_permissions': grouped_permissions,
        'search_query': search_query,
        'total_permissions': permissions.count(),
    }
    return render(request, 'admin/permissions.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_events(request):
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all events
    events = Event.objects.select_related('creator', 'category').all()
    
    # Apply search filter
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(creator__username__icontains=search_query)
        )
    
    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_items')
        
        if action == 'delete' and selected_ids:
            Event.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'Successfully deleted {len(selected_ids)} events.')
            return redirect('admin_events')
    
    # Order events by date
    events = events.order_by('-date', '-time')
    
    context = {
        'events': events,
        'search_query': search_query,
        'total_events': events.count(),
    }
    return render(request, 'admin/events.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_categories(request):
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all categories
    categories = EventCategory.objects.all()
    
    # Apply search filter
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_items')
        
        if action == 'delete' and selected_ids:
            EventCategory.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'Successfully deleted {len(selected_ids)} categories.')
            return redirect('admin_categories')
    
    # Order categories by name
    categories = categories.order_by('name')
    
    context = {
        'categories': categories,
        'search_query': search_query,
        'total_categories': categories.count(),
    }
    return render(request, 'admin/categories.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_registrations(request):
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all registrations
    registrations = EventRegistration.objects.select_related('user', 'event').all()
    
    # Apply search filter
    if search_query:
        registrations = registrations.filter(
            Q(user__username__icontains=search_query) |
            Q(event__title__icontains=search_query) |
            Q(role__icontains=search_query)
        )
    
    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_items')
        
        if action == 'delete' and selected_ids:
            EventRegistration.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'Successfully deleted {len(selected_ids)} registrations.')
            return redirect('admin_registrations')
    
    # Order registrations by date
    registrations = registrations.order_by('-requested_at')
    
    context = {
        'registrations': registrations,
        'search_query': search_query,
        'total_registrations': registrations.count(),
    }
    return render(request, 'admin/registrations.html', context)

@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    # Get all notifications
    notifications = Notification.objects.select_related('recipient', 'sender', 'event').all()
    
    # Debug: Print notification data
    for notification in notifications:
        print(f"Notification: {notification.__dict__}")
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        notifications = notifications.filter(
            Q(message__icontains=search_query) |
            Q(recipient__username__icontains=search_query) |
            Q(sender__username__icontains=search_query)
        )
    
    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_notifications')
        
        if action == 'delete' and selected_ids:
            Notification.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'Successfully deleted {len(selected_ids)} notifications.')
            return redirect('admin_notifications')
    
    # Pagination
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page = request.GET.get('page')
    notifications = paginator.get_page(page)
    
    context = {
        'notifications': notifications,
        'search_query': search_query,
        'total_notifications': notifications.paginator.count if notifications else 0,
    }
    return render(request, 'admin/notifications.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_profiles(request):
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all profiles
    profiles = Profile.objects.select_related('user').all()
    
    # Apply search filter
    if search_query:
        profiles = profiles.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    
    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_items')
        
        if action == 'delete' and selected_ids:
            Profile.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f'Successfully deleted {len(selected_ids)} profiles.')
            return redirect('admin_profiles')
    
    # Order profiles by user's date joined
    profiles = profiles.order_by('-user__date_joined')
    
    context = {
        'profiles': profiles,
        'search_query': search_query,
        'total_profiles': profiles.count(),
    }
    return render(request, 'admin/profiles.html', context)


# def is_admin(user):
#     return user.primary_role == 'ADMIN'

@login_required
def admin_edit_user(request, user_id):
    # Check if user is admin or superuser
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('admin_dashboard')
    
    user_to_edit = get_object_or_404(User, id=user_id)
    current_group = user_to_edit.groups.first()
    
    # If user is superuser, force admin group
    if user_to_edit.is_superuser:
        admin_group = Group.objects.get(name='Admin')
        if not current_group or current_group != admin_group:
            user_to_edit.groups.clear()
            user_to_edit.groups.add(admin_group)
            current_group = admin_group
    
    # If user has no group, set to general_user
    if not current_group and not user_to_edit.is_superuser:
        general_user_group = Group.objects.get(name='General User')
        user_to_edit.groups.add(general_user_group)
        current_group = general_user_group
    
    if request.method == 'POST':
        # Handle basic user information updates
        user_to_edit.username = request.POST.get('username', user_to_edit.username)
        user_to_edit.email = request.POST.get('email', user_to_edit.email)
        user_to_edit.first_name = request.POST.get('first_name', user_to_edit.first_name)
        user_to_edit.last_name = request.POST.get('last_name', user_to_edit.last_name)
        
        # Handle role change
        new_group_id = request.POST.get('primary_role')
        if new_group_id and (request.user.is_superuser or request.user.is_staff) and not user_to_edit.is_superuser:
            try:
                new_group = Group.objects.get(id=new_group_id)
                if new_group.name in ['Admin', 'Manager']:
                    if not request.user.is_superuser:
                        messages.error(request, 'Only superusers can assign admin or manager roles.')
                    else:
                        user_to_edit.groups.clear()
                        user_to_edit.groups.add(new_group)
                        messages.success(request, f'User role changed to {new_group.name}.')
                else:
                    user_to_edit.groups.clear()
                    user_to_edit.groups.add(new_group)
                    messages.success(request, f'User role changed to {new_group.name}.')
            except Group.DoesNotExist:
                messages.error(request, 'Invalid role selected.')
        
        # Handle status fields - only superusers can modify these
        if request.user.is_superuser:
            is_active = request.POST.get('is_active') == 'on'
            is_staff = request.POST.get('is_staff') == 'on'
            is_superuser = request.POST.get('is_superuser') == 'on'
            
            # If making user superuser, ensure they're in admin group
            if is_superuser and not user_to_edit.is_superuser:
                admin_group = Group.objects.get(name='Admin')
                user_to_edit.groups.clear()
                user_to_edit.groups.add(admin_group)
            
            # If removing superuser status, set to general user
            if not is_superuser and user_to_edit.is_superuser:
                general_user_group = Group.objects.get(name='General User')
                user_to_edit.groups.clear()
                user_to_edit.groups.add(general_user_group)
            
            user_to_edit.is_active = is_active
            user_to_edit.is_staff = is_staff
            user_to_edit.is_superuser = is_superuser
        
        # Handle date fields
        try:
            last_login = request.POST.get('last_login')
            if last_login:
                user_to_edit.last_login = datetime.strptime(last_login, '%Y-%m-%dT%H:%M:%S')
            
            date_joined = request.POST.get('date_joined')
            if date_joined:
                user_to_edit.date_joined = datetime.strptime(date_joined, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            messages.error(request, 'Invalid date format.')
        
        try:
            user_to_edit.save()
            messages.success(request, 'User information updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
        
        return redirect('admin_users')
    
    # Get all available groups
    available_groups = Group.objects.all()
    
    # Get current group for role display
    current_group = user_to_edit.groups.first()
    role_name = current_group.name if current_group else 'General User'
    
    # Determine role display info
    role_info = {
        'current_role': {
            'bg_color': 'bg-emerald-100',
            'text_color': 'text-emerald-800'
        }
    }
    
    context = {
        'user': user_to_edit,
        'available_groups': available_groups,
        'current_role': current_group,
        'role_name': role_name,
        'role_info': role_info,
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff,
    }
    
    return render(request, 'admin/admin_edit_user.html', context)


# @login_required
# def user_home(request):
#========================== 2. convert FBV to CBV===================================
class UserHomeView(LoginRequiredMixin,TemplateView):
    template_name= 'user_home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        
    
        user_type="General"
        if self.request.user.is_superuser:
            user_type="Super_user"

        # Get events for the current user
        # system_events = Event.objects.all
        user_events = Event.objects.filter(creator=self.request.user)
        
        # Get public events
        public_events = Event.objects.filter(visibility='PUBLIC')
        public_events_count = public_events.count()
        
        # Get user's notifications
        notifications = Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-timestamp')[:10]  # Get last 10 notifications

        # My attended events
        my_activities = Event.objects.filter(
            registrations__user=self.request.user,
            registrations__role__in=['VOLUNTEER', 'PARTICIPANT'],
            registrations__status='APPROVED'
        ).distinct()

        # Get role information for each activity
        activities_with_roles = []
        for activity in my_activities:
            registration = EventRegistration.objects.filter(
                event=activity,
                user=self.request.user,
                status='APPROVED'
            ).first()
            activities_with_roles.append({
                'event': activity,
                'role': registration.role if registration else None
            })
        
        context = {
            'user_type':user_type,
            'my_activities': activities_with_roles,
            'user_events': user_events,
            # 'system_events': system_events,
            'public_events': public_events,
            'public_events_count': public_events_count,
            'notifications': notifications,
        }
        return context

@login_required
def user_profile(request):
    # Get the user's profile with related data
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)
    
    # Get user's event registrations
    registrations = EventRegistration.objects.filter(
        user=user
    ).select_related('event').order_by('-requested_at')
    
    # Get user's created events
    created_events = Event.objects.filter(
        creator=user
    ).order_by('-date', '-time')
    
    # Get user's managed events
    managed_events = Event.objects.filter(
        managers=user
    ).order_by('-date', '-time')
    
    context = {
        'user': user,
        'profile': profile,
        'registrations': registrations,
        'created_events': created_events,
        'managed_events': managed_events,
    }
    return render(request, 'user_profile.html', context)

# @login_required
# def manager_dashboard(request):
#========================== 1. convert FBV to CBV===================================
class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'manager_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    # Get all events
        events = Event.objects.all()
        
        # Get events for the current user
        user_events = Event.objects.filter(Q(creator=self.request.user) | Q(managers=self.request.user))
        user_total_events = user_events
        
        # Get upcoming events (events with dates in the future)
        user_upcoming_events = user_events.filter(date__gte=timezone.now().date())
        # system_upcoming_events = Event.objects.filter(date__gte=timezone.now().date())
        
        # Get past events (events with dates in the past)
        user_past_events = user_events.filter(date__lt=timezone.now().date())
        # system_past_events = Event.objects.filter(date__lt=timezone.now().date())

        # system_today_events = Event.objects.filter(date=timezone.now().date())
        # user_today_events = user_events.filter(date=timezone.now().date())

        events_type, event_list_title = get_filtered_events(user_events, self.request)
        
        context = {
            'event': events,  # For total count
            'user_total_events_count': user_total_events.count(),
            # 'system_total_events_count': events.count(),
            # 'system_total_users_count': system_upcoming_events.count(),
            'user_upcoming_events_count': user_upcoming_events.count(),
            # 'system_upcoming_events_count': system_upcoming_events.count(),
            'user_past_events_count': user_past_events.count(),
            # 'system_past_events_count': system_past_events.count(),
            'events_list': user_events,  # For the event list
            'event_list_title': event_list_title,
            'user_events_type': events_type
        }
        
        return context

# @login_required
# def user_activity(request):
    # Get all events
    # events = Event.objects.all()
#========================== 3. convert FBV to CBV===================================
class UserActivityView(LoginRequiredMixin,TemplateView):
    template_name = 'user_activity.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    
        # Get events where user is a manager
        as_a_manager = Event.objects.filter(managers=self.request.user)
        
        # Get events where user is a volunteer through EventRegistration
        as_a_volunteer = Event.objects.filter(
            registrations__user=self.request.user,
            registrations__role='VOLUNTEER',
            registrations__status='APPROVED'
        )
        
        # Get events where user is a participant through EventRegistration
        as_a_participant = Event.objects.filter(
            registrations__user=self.request.user,
            registrations__role='PARTICIPANT',
            registrations__status='APPROVED'
        )

        # Get the activity type from self.request
        activity_type = self.request.GET.get('type', 'all')
        activity_title = "Today's Activities"  # Default title

        # Filter events based on activity type
        if activity_type == 'manager':
            filtered_events = as_a_manager
            activity_title = "Manager Activities"
        elif activity_type == 'volunteer':
            filtered_events = as_a_volunteer
            activity_title = "Volunteer Activities"
        elif activity_type == 'participant':
            filtered_events = as_a_participant
            activity_title = "Participant Activities"
        elif activity_type == 'upcoming':
            # Combine and filter for upcoming events
            filtered_events = Event.objects.filter(
                Q(id__in=as_a_manager.values_list('id', flat=True)) |
                Q(id__in=as_a_volunteer.values_list('id', flat=True)) |
                Q(id__in=as_a_participant.values_list('id', flat=True)),
                date__gte=timezone.now().date()
            )
            activity_title = "Upcoming Activities"
        elif activity_type == 'past':
            # Combine and filter for past events
            filtered_events = Event.objects.filter(
                Q(id__in=as_a_manager.values_list('id', flat=True)) |
                Q(id__in=as_a_volunteer.values_list('id', flat=True)) |
                Q(id__in=as_a_participant.values_list('id', flat=True)),
                date__lt=timezone.now().date()
            )
            activity_title = "Past Activities"
        else:
            # Combine and filter for today's events
            filtered_events = Event.objects.filter(
                Q(id__in=as_a_manager.values_list('id', flat=True)) |
                Q(id__in=as_a_volunteer.values_list('id', flat=True)) |
                Q(id__in=as_a_participant.values_list('id', flat=True)),
                date=timezone.now().date()
            )
            activity_title = "Today's Activities"

        # Get registration information for each event
        events_with_roles = []
        for event in filtered_events:
            role = None
            if event in as_a_manager:
                role = 'MANAGER'
            else:
                registration = EventRegistration.objects.filter(
                    event=event,
                    user=self.request.user,
                    status='APPROVED'
                ).first()
                if registration:
                    role = registration.role
            events_with_roles.append({
                'event': event,
                'role': role
            })

        context = {
            'events': filtered_events,
            'events_with_roles': events_with_roles,
            'activity_title': activity_title,
            'activity_type': activity_type,
            'filtered_events': filtered_events.count(),
            'filtered_events_list': events_with_roles,
            'as_a_manager': as_a_manager.count(),
            'as_a_volunteer': as_a_volunteer.count(),
            'as_a_participant': as_a_participant.count(),
            # 'manager_count': as_a_manager,
            # 'volunteer_count': as_a_volunteer,
            # 'participant_count': as_a_participant,
        }

        return context

@login_required
def add_an_event(request):
        
    if request.method == 'POST':
        try:
            # Get form data
            event_name = request.POST.get('event_name')
            event_category = request.POST.get('event_category')
            event_date = request.POST.get('event_date')
            event_time = request.POST.get('event_time')
            event_description = request.POST.get('event_description')
            event_location = request.POST.get('event_location')
            event_tags = request.POST.get('event_tags')
            event_visibility = request.POST.get('event_visibility')
            event_cover = request.FILES.get('event_cover')
            max_attendees = request.POST.get('max_attendees')

            # Validate required fields
            if not all([event_name, event_category, event_date, event_time, event_description, event_location, event_visibility]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'add_an_event.html')

            # Get or create category
            category, created = EventCategory.objects.get_or_create(name=event_category)

            # Create event
            event = Event(
                title=event_name,
                date=event_date,
                time=event_time,
                description=event_description,
                location=event_location,
                tags=event_tags,
                visibility=event_visibility.upper(),  # Convert to uppercase to match choices
                event_cover=event_cover,
                max_attendees=max_attendees if max_attendees else None,
                category=category,
                creator=request.user  # Set the creator to the current user
            )
            event.save()

            messages.success(request, 'Event created successfully!')
            return redirect('add_an_event')  # Redirect to user's home page or event list

        except Exception as e:
            messages.error(request, f'An error occurred while creating the event: {str(e)}')
            return render(request, 'add_an_event.html')

    # GET request - show the form
    categories = EventCategory.objects.all()
    return render(request, 'add_an_event.html', {'categories': categories})

@login_required
def invite_user(request, event_id):
    if request.method == 'POST':
        form = InviteUserForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            role = form.cleaned_data['role']
            message = form.cleaned_data['message']
            
            try:
                event = Event.objects.get(event_id=event_id)
                user_to_invite = User.objects.get(id=user_id)
                print(user_to_invite)
                # Check if user is already registered
                existing_registration = EventRegistration.objects.filter(
                    event=event,
                    user=user_to_invite
                ).first()
                
                if existing_registration:
                    if existing_registration.status == 'INVITED':
                        messages.warning(request, f'"{user_to_invite}" has already been invited.')
                    elif existing_registration.status == 'APPROVED':
                        messages.warning(request, f'"{user_to_invite}" is already registered.')
                    else:
                        messages.warning(request, f'"{user_to_invite}" has a pending request.')
                else:
                    # Create new registration
                    registration = EventRegistration.objects.create(
                        user=user_to_invite,
                        event=event,
                        role=role,
                        status='INVITED',
                        invited_at=timezone.now()
                    )
                    
                    # Create notification
                    Notification.objects.create(
                        recipient=user_to_invite,
                        sender=request.user,
                        event=event,
                        notification_type='EVENT_INVITE_PARTICIPANT' if role == 'PARTICIPANT' else 'EVENT_INVITE_VOLUNTEER',
                        message=f'You have invited "{user_to_invite}" to join "{event.title}" as a {registration.get_role_display()}.'
                    )
                    
                    messages.success(request, f'Successfully invited "{user_to_invite}" as a {registration.get_role_display()}.')
                
            except (Event.DoesNotExist, User.DoesNotExist):
                messages.error(request, 'Invalid event or user.')
                return redirect('manager_dashboard')
                
    return redirect('manage_spacific_event', event_id=event_id)

# @login_required
# def manage_spacific_event(request, event_id):
#========================== 4. convert FBV to CBV===================================
class ManageSpacificEventView(LoginRequiredMixin, TemplateView):
    template_name = 'manage_spacific_event.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = self.kwargs.get('event_id')
        
        try:
            event = Event.objects.get(event_id=event_id)
            
            # Get events for the current user
            user_events = Event.objects.filter(creator=self.request.user)
            
            # Use the helper function to get filtered events
            events_type, event_list_title = get_filtered_events(user_events, self.request)

            # Get current server time
            current_time = timezone.now()
            today = current_time.date()

            # Get pending requests for this event
            pending_requests = EventRegistration.objects.filter(
                event=event,
                status='PENDING_APPROVAL'
            ).select_related('user')

            # Get notifications for this event
            notifications_list = Notification.objects.filter(
                event=event
            ).order_by('-timestamp')

            # Get event attendees (both participants and volunteers)
            volunteers = EventRegistration.objects.filter(
                event=event,
                role='VOLUNTEER',
                status='APPROVED'
            ).select_related('user')
            
            participants = EventRegistration.objects.filter(
                event=event,
                role='PARTICIPANT',
                status='APPROVED'
            ).select_related('user')

            # Get user's registration for this event
            user_registration = EventRegistration.objects.filter(
                event=event,
                user=self.request.user,
                status='APPROVED'
            ).first()

            # Check if user is an approved volunteer for this event
            is_volunteer = EventRegistration.objects.filter(
                event=event,
                user=self.request.user,
                role='VOLUNTEER',
                status='APPROVED'
            ).exists()

            # Handle user search with improved query
            searched_users = None
            if self.request.GET.get('user_search_query'):
                search_query = self.request.GET.get('user_search_query').strip()
                if len(search_query) >= 2:  # Only search if query is at least 2 characters
                    # Split the search query into words for better matching
                    search_terms = search_query.split()
                    
                    # Start with a base queryset excluding the current user
                    base_query = User.objects.filter(is_superuser=False).exclude(id=self.request.user.id)
                    
                    # Build the query dynamically based on search terms
                    query = Q()
                    for term in search_terms:
                        term_query = (
                            Q(username__icontains=term) |
                            Q(email__icontains=term) |
                            Q(first_name__icontains=term) |
                            Q(last_name__icontains=term)
                        )
                        query &= term_query
                    
                    # Apply the search query
                    searched_users = base_query.filter(query).distinct()[:10]  # Limit to 10 results
                    
                    # Add a message if no results found
                    if not searched_users:
                        messages.info(self.request, f'No users found matching "{search_query}"')
                else:
                    messages.warning(self.request, 'Please enter at least 2 characters to search')

            # Create invitation form
            invite_form = InviteUserForm()

            context = {
                'event': event,
                'events_type': events_type,
                'event_list_title': event_list_title,
                'current_time': current_time,
                'today': today,
                'is_running': is_event_running(event.date, event.time),
                'pending_requests': pending_requests,
                'notifications_list': notifications_list,
                'volunteers': volunteers,
                'participants': participants,
                'searched_users': searched_users,
                'invite_form': invite_form,
                'user_registration': user_registration,
                'is_volunteer': is_volunteer,
            }
            return context
        except Event.DoesNotExist:
            messages.error(self.request, 'Event not found.')
            return redirect('manager_dashboard')
    

# @login_required
# def manager_update_event(request, event_id):
#========================== 5. convert FBV to CBV===================================
class ManagerUpdateEventView(LoginRequiredMixin, TemplateView):
    template_name = 'update_event.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_id = self.kwargs.get('event_id')
        
        try:
            event = Event.objects.get(event_id=event_id)
            if self.request.user != event.creator and self.request.user not in event.managers.all():
                messages.error(self.request, "You don't have permission to update this event.")
                return redirect('manager_dashboard')
                
            form = EventUpdateForm(instance=event)
            context.update({
                'event': event,
                'form': form,
                'uuid': event_id
            })
            return context
            
        except Event.DoesNotExist:
            messages.error(self.request, "Event not found.")
            return redirect('manager_dashboard')
    
    def post(self, request, *args, **kwargs):
        event_id = self.kwargs.get('event_id')
        try:
            event = Event.objects.get(event_id=event_id)
            form = EventUpdateForm(request.POST, request.FILES, instance=event)
            if form.is_valid():
                form.save()
                messages.success(request, 'Event updated successfully!')
                return redirect('manage_spacific_event', event_id=event_id)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return self.get(request, *args, **kwargs)
        except Event.DoesNotExist:
            messages.error(request, "Event not found.")
            return redirect('manager_dashboard')

@login_required
def manager_delete_event(request, event_id):
    try:
        event = Event.objects.get(event_id=event_id)
        if request.method == 'POST':
            event.delete()
            messages.success(request, 'Event deleted successfully!')
            return redirect('manager_dashboard')
        return redirect('manage_spacific_event', event_id=event_id)
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('manager_dashboard')

@login_required
def accept_request(request, request_id):
    try:
        registration = EventRegistration.objects.get(id=request_id)
        if request.method == 'POST':
            registration.status = 'APPROVED'
            registration.processed_at = timezone.now()
            registration.save()

            # Create notification
            Notification.objects.create(
                recipient=registration.user,
                sender=request.user,
                event=registration.event,
                notification_type='REQUEST_APPROVED',
                message=f'You have accepted the request from "{registration.user}" to join "{registration.event.title}" as a {registration.get_role_display()}.'
            )

            messages.success(request, 'Request approved successfully.')
            base_url = reverse('manage_spacific_event', kwargs={'event_id': registration.event.event_id})
    
            # ফ্র্যাগমেন্ট যোগ করুন
            url_with_fragment = f"{base_url}#requests" # এখানে 'requests' হলো আপনার সেকশনের আইডি

        return redirect(url_with_fragment)
        # return redirect('manage_spacific_event', event_id=registration.event.event_id)
    except EventRegistration.DoesNotExist:
        messages.error(request, 'Request not found.')
        return redirect('manager_dashboard')

@login_required
def reject_request(request, request_id):
    try:
        registration = EventRegistration.objects.get(id=request_id)
        if request.method == 'POST':
            registration.status = 'REJECTED'
            registration.processed_at = timezone.now()
            registration.save()

            # Create notification
            Notification.objects.create(
                recipient=registration.user,
                sender=request.user,
                event=registration.event,
                notification_type='REQUEST_REJECTED',
                message=f'Your request to join {registration.event.title} as a {registration.get_role_display()} has been rejected.'
            )

            messages.error(request, 'Request rejected successfully.')
            base_url = reverse('manage_spacific_event', kwargs={'event_id': registration.event.event_id})
            url_with_fragment = f"{base_url}#requests"
        return redirect(url_with_fragment)
        #return redirect('manage_spacific_event', event_id=registration.event.event_id)
    except EventRegistration.DoesNotExist:
        messages.error(request, 'Request not found.')
        return redirect('manager_dashboard')

@login_required
def join_event(request, event_id):
    if request.method == 'POST':
        try:
            logger.info(f"Join request received for event {event_id} from user {request.user.username}")
            
            # Get and validate event
            try:
                event = Event.objects.get(event_id=event_id)
            except Event.DoesNotExist:
                logger.error(f"Event {event_id} not found")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Event not found'
                }, status=404)
            
            # Get and validate role
            role = request.POST.get('role', '').upper()
            logger.info(f"Requested role: {role}")
            
            if not role:
                logger.error("No role specified in request")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Role is required'
                }, status=400)
            
            if role not in ['PARTICIPANT', 'VOLUNTEER']:
                logger.error(f"Invalid role specified: {role}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid role specified'
                }, status=400)
            
            # Check existing registration
            existing_registration = EventRegistration.objects.filter(
                event=event,
                user=request.user
            ).first()
            
            if existing_registration:
                if existing_registration.status == 'PENDING_APPROVAL':
                    logger.info(f"User already has pending request for event {event_id}")
                    return JsonResponse({
                        'status': 'warning',
                        'message': 'You already have a pending request for this event'
                    })
                elif existing_registration.status == 'APPROVED':
                    logger.info(f"User already registered for event {event_id}")
                    return JsonResponse({
                        'status': 'warning',
                        'message': 'You are already registered for this event'
                    })
                elif existing_registration.status == 'REJECTED':
                    logger.info(f"Deleting previous rejected registration for event {event_id}")
                    existing_registration.delete()
                else:
                    logger.info(f"User has existing invitation for event {event_id}")
                    return JsonResponse({
                        'status': 'warning',
                        'message': 'You already have an invitation for this event'
                    })
            
            # Create new registration
            try:
                registration = EventRegistration.objects.create(
                    user=request.user,
                    event=event,
                    role=role,
                    status='PENDING_APPROVAL',
                    requested_at=timezone.now()
                )
                logger.info(f"Created new registration for event {event_id}")
                
                # Create notification
                Notification.objects.create(
                    recipient=event.creator,
                    sender=request.user,
                    event=event,
                    notification_type='JOIN_REQUEST_PARTICIPANT' if role == 'PARTICIPANT' else 'JOIN_REQUEST_VOLUNTEER',
                    message=f'"{request.user.get_full_name() or request.user.username}" sent a request to join  The "{event.title}" as a {registration.get_role_display()}.'
                )
                logger.info(f"Created notification for event creator")
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Your request to join as a {registration.get_role_display()} has been sent!'
                })
                
            except Exception as e:
                logger.error(f"Error creating registration: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error creating registration'
                }, status=500)
            
        except Exception as e:
            logger.error(f"Unexpected error in join_event: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@login_required
def accept_invitation(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(event_id=event_id)
            registration = EventRegistration.objects.get(
                event=event,
                user=request.user,
                status='INVITED'
            )
            
            # Clear previous notifications for this event and user
            Notification.objects.filter(
                event=event,
                recipient=request.user,
                notification_type__in=['INVITED', 'INVITE_ACCEPTED', 'INVITE_DECLINED']
            ).delete()
            
            registration.status = 'APPROVED'
            registration.processed_at = timezone.now()
            registration.save()
            
            # Create notification for event creator
            Notification.objects.create(
                recipient=event.creator,
                sender=request.user,
                event=event,
                notification_type='INVITE_ACCEPTED',
                message=f'{request.user.get_full_name() or request.user.username} has accepted your invitation to join {event.title} as a {registration.get_role_display()}.'
            )
            
            # Create notification for the user who accepted
            Notification.objects.create(
                recipient=request.user,
                sender=event.creator,
                event=event,
                notification_type='INVITE_ACCEPTED',
                message=f'You have successfully joined {event.title} as a {registration.get_role_display()}.'
            )
            
            messages.success(request, f'You have successfully joined {event.title} as a {registration.get_role_display()}.')
            
        except (Event.DoesNotExist, EventRegistration.DoesNotExist):
            messages.error(request, 'Invalid event or invitation.')
        except Exception as e:
            messages.error(request, 'An error occurred while processing your request.')
            
    return redirect('user_home')

@login_required
def decline_invitation(request, event_id):
    if request.method == 'POST':
        try:
            event = Event.objects.get(event_id=event_id)
            registration = EventRegistration.objects.get(
                event=event,
                user=request.user,
                status='INVITED'
            )
            
            # Clear previous notifications for this event and user
            Notification.objects.filter(
                event=event,
                recipient=request.user,
                notification_type__in=['INVITED', 'INVITE_ACCEPTED', 'INVITE_DECLINED']
            ).delete()
            
            registration.status = 'REJECTED'
            registration.processed_at = timezone.now()
            registration.save()
            
            # Create notification for event creator
            Notification.objects.create(
                recipient=event.creator,
                sender=request.user,
                event=event,
                notification_type='INVITE_DECLINED',
                message=f'{request.user.get_full_name() or request.user.username} has declined your invitation to join {event.title} as a {registration.get_role_display()}.'
            )
            
            # Create notification for the user who declined
            Notification.objects.create(
                recipient=request.user,
                sender=event.creator,
                event=event,
                notification_type='INVITE_DECLINED',
                message=f'You have declined the invitation to join {event.title} as a {registration.get_role_display()}.'
            )
            
            messages.success(request, f'You have declined the invitation to join {event.title}.')
            
        except (Event.DoesNotExist, EventRegistration.DoesNotExist):
            messages.error(request, 'Invalid event or invitation.')
        except Exception as e:
            messages.error(request, 'An error occurred while processing your request.')
            
    return redirect('user_home')





def test_email(request):
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can test email configuration.')
        return redirect('admin_dashboard')
    
    try:
        send_mail(
            subject='Test Email from EventPro',
            message='This is a test email to verify your email configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )
        messages.success(request, 'Test email sent successfully! Please check your inbox.')
    except Exception as e:
        messages.error(request, f'Failed to send test email: {str(e)}')
    
    return redirect('admin_dashboard')



class AdminUserPasswordResetView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/admin_edit_user.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(request, 'You do not have permission to reset passwords.')
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        context['user'] = user
        return context
    
    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not new_password1 or not new_password2:
            messages.error(request, 'Both password fields are required.')
            return redirect('admin_user_edit', user_id=user_id)
        
        if new_password1 != new_password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('admin_user_edit', user_id=user_id)
        
        # Temporarily deactivate the user
        user.is_active = False
        user.save()
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.user_id))
        
        # Prepare email context
        context = {
            'user': user,
            'new_password': new_password1,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': request.get_host(),
            'uid': uid,
            'token': token,
            'site_name': settings.SITE_NAME,
        }
        
        try:
            # Render email content
            email_content = render_to_string('admin/email/password_reset_email.html', context)
            
            # Log email attempt
            logger.info(f"Attempting to send password reset email to {user.email}")
            
            # Send email
            send_mail(
                subject='Your Password Has Been Reset',
                message=email_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
                html_message=email_content,
            )
            
            logger.info(f"Successfully sent password reset email to {user.email}")
            
            # Set the new password
            user.set_password(new_password1)
            user.save()
            
            messages.success(request, 'Password has been reset and activation email has been sent to the user.')
            
            # Create notification for the user
            Notification.objects.create(
                recipient=user,
                sender=request.user,
                notification_type='PASSWORD_RESET',
                message=f'Your password has been reset by {request.user.get_full_name() or request.user.username}. Please check your email for activation instructions.'
            )
            
        except Exception as e:
            # Log the error
            logger.error(f"Error sending password reset email to {user.email}: {str(e)}")
            
            # If email fails, reactivate the user and show error
            user.is_active = True
            user.save()
            messages.error(request, f'Error sending email: {str(e)}. Please check your email configuration.')
        
        return redirect('admin_user_edit', user_id=user_id)

class CustomPasswordChangeView(BasePasswordChangeView):
    template_name = 'user_profile.html'
    success_url = reverse_lazy('user_profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your password has been successfully changed!')
        return response

class UpdateProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'user_profile.html'
    success_url = reverse_lazy('user_profile')
    form_class = ProfileUpdateForm

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_initial(self):
        initial = super().get_initial()
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been successfully updated!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context





    