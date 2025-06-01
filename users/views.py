from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from tasks.models import Event, EventCategory,Profile,User, EventRegistration, Notification
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time
from django.db.models import Q
from .forms import InviteUserForm
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

def is_event_running(event_date, event_time):
    """Helper function to check if an event is currently running"""
    current_time = timezone.now()
    current_date = current_time.date()
    current_time_only = current_time.time()
    
    return (event_date == current_date and 
            event_time and current_time_only >= event_time)

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

@login_required
def admin_dashboard(request):
    return render(request, 'admin/admin_home.html')

@login_required
def user_home(request):
    # Get events for the current user
    system_events = Event.objects.all()
    user_events = Event.objects.filter(creator=request.user)
    
    # Get public events
    public_events = Event.objects.filter(visibility='PUBLIC')
    public_events_count = public_events.count()
    
    # Get user's notifications
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-timestamp')[:10]  # Get last 10 notifications
    
    context = {
        'user_events': user_events,
        'system_events': system_events,
        'public_events': public_events,
        'public_events_count': public_events_count,
        'notifications': notifications,
    }
    return render(request, 'user_home.html', context)

@login_required
def manager_dashboard(request):
    # Get all events
    events = Event.objects.all()
    
    # Get events for the current user
    user_events = Event.objects.filter(creator=request.user)
    user_total_events = user_events
    
    # Get upcoming events (events with dates in the future)
    user_upcoming_events = user_events.filter(date__gte=timezone.now().date())
    system_upcoming_events = Event.objects.filter(date__gte=timezone.now().date())
    
    # Get past events (events with dates in the past)
    user_past_events = user_events.filter(date__lt=timezone.now().date())
    system_past_events = Event.objects.filter(date__lt=timezone.now().date())

    system_today_events = Event.objects.filter(date=timezone.now().date())
    user_today_events = user_events.filter(date=timezone.now().date())

    events_type, event_list_title = get_filtered_events(user_events, request)
    
    context = {
        'event': events,  # For total count
        'user_total_events_count': user_total_events.count(),
        'system_total_events_count': events.count(),
        'system_total_users_count': system_upcoming_events.count(),
        'user_upcoming_events_count': user_upcoming_events.count(),
        'system_upcoming_events_count': system_upcoming_events.count(),
        'user_past_events_count': user_past_events.count(),
        'system_past_events_count': system_past_events.count(),
        'events_list': user_events,  # For the event list
        'event_list_title': event_list_title,
        'user_events_type': events_type
    }
    
    return render(request, 'manager_dashboard.html', context)

@login_required
def user_activity(request):
    return render(request, 'user_activity.html')

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
            event_image_url = request.POST.get('event_image_url')
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
                image_url=event_image_url,
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
                
                # Check if user is already registered
                existing_registration = EventRegistration.objects.filter(
                    event=event,
                    user=user_to_invite
                ).first()
                
                if existing_registration:
                    if existing_registration.status == 'INVITED':
                        messages.warning(request, f'{user_to_invite.get_full_name()} has already been invited.')
                    elif existing_registration.status == 'APPROVED':
                        messages.warning(request, f'{user_to_invite.get_full_name()} is already registered.')
                    else:
                        messages.warning(request, f'{user_to_invite.get_full_name()} has a pending request.')
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
                        message=f'You have been invited to join {event.title} as a {registration.get_role_display()}.'
                    )
                    
                    messages.success(request, f'Successfully invited {user_to_invite.get_full_name()} as a {registration.get_role_display()}.')
                
            except (Event.DoesNotExist, User.DoesNotExist):
                messages.error(request, 'Invalid event or user.')
                return redirect('manager_dashboard')
                
    return redirect('manage_spacific_event', event_id=event_id)

@login_required
def manage_spacific_event(request, event_id):
    try:
        event = Event.objects.get(event_id=event_id)
        
        # Get events for the current user
        user_events = Event.objects.filter(creator=request.user)
        
        # Use the helper function to get filtered events
        events_type, event_list_title = get_filtered_events(user_events, request)

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
        event_attendees = EventRegistration.objects.filter(
            event=event,
            status='APPROVED'
        ).select_related('user')

        # Handle user search with improved query
        searched_users = None
        if request.GET.get('user_search_query'):
            search_query = request.GET.get('user_search_query').strip()
            if len(search_query) >= 2:  # Only search if query is at least 2 characters
                # Split the search query into words for better matching
                search_terms = search_query.split()
                
                # Start with a base queryset excluding the current user
                base_query = User.objects.filter(is_superuser=False).exclude(id=request.user.id)
                
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
                    messages.info(request, f'No users found matching "{search_query}"')
            else:
                messages.warning(request, 'Please enter at least 2 characters to search')

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
            'event_attendees': event_attendees,
            'searched_users': searched_users,
            'invite_form': invite_form,
        }
        return render(request, 'manage_spacific_event.html', context)
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('manager_dashboard')

@login_required
def manager_update_event(request, event_id):
    try:
        event = Event.objects.get(event_id=event_id)
        if request.method == 'POST':
            # Handle event update
            event.title = request.POST.get('event_name', event.title)
            event.description = request.POST.get('event_description', event.description)
            event.date = request.POST.get('event_date', event.date)
            event.time = request.POST.get('event_time', event.time)
            event.location = request.POST.get('event_location', event.location)
            event.visibility = request.POST.get('event_visibility', event.visibility).upper()
            event.image_url = request.POST.get('event_image_url', event.image_url)
            event.max_attendees = request.POST.get('max_attendees', event.max_attendees)
            event.tags = request.POST.get('event_tags', event.tags)
            
            # Update category if provided
            category_name = request.POST.get('event_category')
            if category_name:
                category, created = EventCategory.objects.get_or_create(name=category_name)
                event.category = category
            
            event.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('manager_dashboard')
            
        context = {
            'event': event,
            'categories': EventCategory.objects.all()
        }
        return render(request, 'update_event.html', context)
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('manager_dashboard')

@login_required
def manager_delete_event(request, event_id):
    try:
        event = Event.objects.get(event_id=event_id)
        if request.method == 'POST':
            event.delete()
            messages.success(request, 'Event deleted successfully!')
            return redirect('manager_dashboard')
        return render(request, 'confirm_delete.html', {'event': event})
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
                message=f'Your request to join {registration.event.title} as a {registration.get_role_display()} has been approved.'
            )

            messages.success(request, 'Request approved successfully.')
        return redirect('manage_spacific_event', event_id=registration.event.event_id)
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

            messages.success(request, 'Request rejected successfully.')
        return redirect('manage_spacific_event', event_id=registration.event.event_id)
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
                    message=f'{request.user.get_full_name() or request.user.username} wants to join {event.title} as a {registration.get_role_display()}.'
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
            
            messages.success(request, f'You have declined the invitation to join {event.title}.')
            
        except (Event.DoesNotExist, EventRegistration.DoesNotExist):
            messages.error(request, 'Invalid event or invitation.')
        except Exception as e:
            messages.error(request, 'An error occurred while processing your request.')
            
    return redirect('user_home')
