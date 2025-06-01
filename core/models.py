from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    ROLE_CHOICES = [
        ('GENERAL_USER', 'General User'),
        ('EVENT_MANAGER', 'Event Manager'),
        ('VOLUNTEER', 'Volunteer'),
        ('PARTICIPANT', 'Participant'),
        ('ADMIN', 'Admin'),
    ]
    
    # Unique identifier for the user
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Make email field unique
    email = models.EmailField(unique=True, verbose_name='email address')
    
    # Inherits username, first_name, last_name, password, etc.
    primary_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='GENERAL_USER',
        help_text='Defines the primary system-wide role of the user.'
    )

    def __str__(self):
        return self.username

    def is_general_user(self):
        return self.primary_role == 'GENERAL_USER'
