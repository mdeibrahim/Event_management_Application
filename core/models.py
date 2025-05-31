from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    ROLE_CHOICES = [
        ('GENERAL_USER', 'General User'),
    ]
    
    # Unique identifier for the user
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Inherits username, first_name, last_name, email, password, etc.
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
