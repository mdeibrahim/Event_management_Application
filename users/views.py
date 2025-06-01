from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from tasks.models import Event, EventCategory
from django.contrib import messages
from django.utils import timezone

# Create your views here.

@login_required
def admin_dashboard(request):
    return render(request, 'admin/admin_home.html')

@login_required
def user_home(request):
    return render(request, 'user_home.html')

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

    type = request.GET.get('type')
    if type == 'total':
        events_type = user_total_events
        event_list_title = "Total Events"
    elif type == 'upcoming':
        events_type = user_upcoming_events
        event_list_title = "Upcoming Events"
    elif type == 'past':
        events_type = user_past_events
        event_list_title = "Past Events"
    else:
        events_type = user_today_events
        event_list_title = "Today's Events"
    
    context = {
        'event': events,  # For total count
        'user_total_events_count': user_total_events.count(),
        'system_total_events_count': events.count(),
        'system_total_users_count': system_upcoming_events.count(),
        'user_upcoming_events_count': user_upcoming_events.count(),
        'system_upcoming_events_count': system_upcoming_events.count(),
        'user_past_events_count': user_past_events.count(),
        'system_past_events_count': system_past_events.count(),
        # 'user_total_participants_count': user_events.count(),
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
def manage_spacific_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        context = {
            'event': event,
        }
        return render(request, 'manage_spacific_event.html', context)
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('manager_dashboard')

@login_required
def manager_update_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
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
        event = Event.objects.get(id=event_id)
        if request.method == 'POST':
            event.delete()
            messages.success(request, 'Event deleted successfully!')
            return redirect('manager_dashboard')
        return render(request, 'confirm_delete.html', {'event': event})
    except Event.DoesNotExist:
        messages.error(request, 'Event not found.')
        return redirect('manager_dashboard')
