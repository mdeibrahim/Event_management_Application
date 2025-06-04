from django.db import models
from django.contrib.auth.models import AbstractUser # Using AbstractUser for easier extension
from django.conf import settings # To use AUTH_USER_MODEL
import os
import uuid
from django.contrib.auth import get_user_model

# Custom User Model (if you decide to extend the default User significantly later)
# For now, we can use Django's built-in User and a separate Profile model.
# If you use AbstractUser, ensure you set AUTH_USER_MODEL = 'your_app.User' in settings.py

User = get_user_model()

def user_profile_image_path(instance, filename):
    # Generate path: media/profiles/user_id/filename
    ext = filename.split('.')[-1]
    filename = f"profile_{instance.user.id}.{ext}"
    return os.path.join('profiles', str(instance.user.id), filename)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('PREFER_NOT_TO_SAY', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=user_profile_image_path, blank=True, null=True)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        # Delete old image if it exists and new image is being uploaded
        if self.pk:
            try:
                old_instance = Profile.objects.get(pk=self.pk)
                if old_instance.profile_picture and self.profile_picture and old_instance.profile_picture != self.profile_picture:
                    if os.path.isfile(old_instance.profile_picture.path):
                        os.remove(old_instance.profile_picture.path)
            except Profile.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the image file when profile is deleted
        if self.profile_picture:
            if os.path.isfile(self.profile_picture.path):
                os.remove(self.profile_picture.path)
        super().delete(*args, **kwargs)

class EventCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Event Categories"

class Event(models.Model):
    VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
    ]

    # Unique identifier for the event
    event_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    # Managers field will store users who have managerial roles for this event.
    # The creator is automatically a manager. Others can be invited.
    managers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='managed_events', blank=True)
    
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PUBLIC')
    secret_code = models.CharField(max_length=50, blank=True, null=True, unique=True) # For private events
    
    event_cover = models.ImageField(upload_to='images/', blank=True, null=True) # Or use ImageField
    max_attendees = models.PositiveIntegerField(blank=True, null=True) # Optional
    tags = models.CharField(max_length=255, blank=True, null=True) # e.g., "tech,python,django"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.event_id})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.creator:
            # Automatically add the creator to the managers list
            self.managers.add(self.creator)

class EventRegistration(models.Model):
    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('PARTICIPANT', 'Participant'),
        ('VOLUNTEER', 'Volunteer'),
    ]
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'), # User requested to join
        ('APPROVED', 'Approved'),               # Request approved or invite accepted
        ('REJECTED', 'Rejected'),               # Request rejected or invite declined by user
        ('INVITED', 'Invited'),                 # Manager invited user
        ('CANCELLED_BY_USER', 'Cancelled by User'), # User cancelled their approved registration
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES) # Participant or Volunteer
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    requested_at = models.DateTimeField(null=True, blank=True) # Timestamp when user requests
    invited_at = models.DateTimeField(null=True, blank=True) # Timestamp when user is invited (for this specific role)
    processed_at = models.DateTimeField(null=True, blank=True) # Timestamp when status changes (approved, rejected etc.)
    
    # attended = models.BooleanField(default=False) # For tracking actual attendance

    class Meta:
        unique_together = ('user', 'event', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.event.title} as {self.get_role_display()}"

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('EVENT_INVITE_PARTICIPANT', 'Event Invitation (Participant)'),
        ('EVENT_INVITE_VOLUNTEER', 'Event Invitation (Volunteer)'),
        ('EVENT_INVITE_MANAGER', 'Event Invitation (Manager)'), # This would trigger adding to Event.managers
        
        ('JOIN_REQUEST_MANAGER', 'Join Request (Manager)'),
        ('JOIN_REQUEST_PARTICIPANT', 'Join Request (Participant)'),
        ('JOIN_REQUEST_VOLUNTEER', 'Join Request (Volunteer)'),

        ('REQUEST_APPROVED', 'Request Approved'),
        ('REQUEST_REJECTED', 'Request Rejected'),
        ('INVITE_ACCEPTED', 'Invitation Accepted'), # User accepted Participant/Volunteer invite
        ('INVITE_DECLINED', 'Invitation Declined'), # User declined Participant/Volunteer invite
        ('MANAGER_INVITE_ACCEPTED', 'Manager Invitation Accepted'), # User accepted Manager invite
        ('MANAGER_INVITE_DECLINED', 'Manager Invitation Declined'), # User declined Manager invite
        ('EVENT_UPDATE', 'Event Details Updated'),
        ('ROLE_ASSIGNED', 'New Role Assigned'), # General role assignment notification
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='event_notifications')
    # registration = models.ForeignKey(EventRegistration, on_delete=models.SET_NULL, null=True, blank=True, related_name='registration_notifications') # Link to specific registration if applicable

    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField(blank=True) # Can be auto-generated based on type or custom
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient.username} re: {self.notification_type}"

    def save(self, *args, **kwargs):
        if not self.message: # Auto-generate message if not provided
            if self.event:
                self.message = f"Notification regarding event: {self.event.title}. Type: {self.get_notification_type_display()}"
            else:
                self.message = f"Notification type: {self.get_notification_type_display()}"
        super().save(*args, **kwargs)