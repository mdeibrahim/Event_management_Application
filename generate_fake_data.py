#!/usr/bin/env python3
"""
Simple fake data generation script for the Event Management System.
Run this from the project root directory.
"""

import os
import sys
import django
import random
from faker import Faker
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_management_project.settings')
django.setup()

# Now import models
from core.models import User
from tasks.models import Profile, EventCategory, Event, EventRegistration, Notification


def create_event_categories():
    """Create basic event categories"""
    categories_data = [
        {'name': 'Technology', 'description': 'Tech conferences, workshops, and meetups'},
        {'name': 'Business', 'description': 'Business networking and professional events'},
        {'name': 'Education', 'description': 'Educational workshops and seminars'},
        {'name': 'Sports', 'description': 'Sports events and competitions'},
        {'name': 'Arts & Culture', 'description': 'Cultural events, exhibitions, and performances'},
        {'name': 'Health & Wellness', 'description': 'Health, fitness, and wellness events'},
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = EventCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories.append(category)
        if created:
            print(f"✓ Created category: {category.name}")
        else:
            print(f"- Category already exists: {category.name}")
    
    return categories


def generate_bd_phone():
    """Generate a Bangladeshi phone number"""
    prefixes = ['013', '015', '016', '017', '018', '019']
    prefix = random.choice(prefixes)
    number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + number


def create_users(count=20):
    """Create fake users with profiles"""
    fake = Faker()
    users = []
    roles = ['GENERAL_USER', 'EVENT_MANAGER', 'VOLUNTEER', 'PARTICIPANT']
    gender_choices = ['MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY']
    
    print(f"\nCreating {count} users...")
    
    for i in range(count):
        # Generate unique username and email
        username = fake.user_name() + str(random.randint(100, 999))
        email = fake.email()
        
        # Ensure uniqueness
        while User.objects.filter(username=username).exists():
            username = fake.user_name() + str(random.randint(100, 999))
        while User.objects.filter(email=email).exists():
            email = fake.email()
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password='password123',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            primary_role=random.choice(roles)
        )
        
        # Create profile
        Profile.objects.create(
            user=user,
            phone_number=generate_bd_phone(),
            age=random.randint(18, 65),
            gender=random.choice(gender_choices)
        )
        
        users.append(user)
        print(f"✓ Created user: {user.username} ({user.email})")
    
    return users


def create_events(users, categories, count=10):
    """Create fake events"""
    fake = Faker()
    events = []
    visibility_choices = ['PUBLIC', 'PRIVATE']
    
    event_titles = [
        'Tech Innovation Summit', 'Business Networking Night', 'Python Workshop',
        'Digital Marketing Masterclass', 'Startup Pitch Competition',
        'Web Development Bootcamp', 'AI Conference', 'Blockchain Seminar',
        'Data Science Meetup', 'Mobile Development Workshop',
        'Cultural Festival', 'Sports Tournament', 'Art Exhibition',
        'Health & Wellness Workshop', 'Community Service Event'
    ]
    
    print(f"\nCreating {count} events...")
    
    for i in range(count):
        # Random future date (1 to 60 days from now)
        event_date = fake.date_between(start_date='today', end_date='+60d')
        event_time = fake.time()
        
        creator = random.choice(users)
        title = random.choice(event_titles) + f" {random.randint(2024, 2025)}"
        visibility = random.choice(visibility_choices)
        
        event = Event.objects.create(
            title=title,
            description=fake.text(max_nb_chars=300),
            category=random.choice(categories),
            date=event_date,
            time=event_time,
            location=fake.address()[:100],  # Limit length
            creator=creator,
            visibility=visibility,
            secret_code=fake.uuid4()[:8] if visibility == 'PRIVATE' else None,
            max_attendees=random.randint(10, 100) if random.choice([True, False]) else None,
            tags=', '.join(fake.words(nb=3))
        )
        
        # Add some random managers
        potential_managers = [u for u in users if u != creator]
        if potential_managers:
            managers_to_add = random.sample(
                potential_managers, 
                min(random.randint(0, 2), len(potential_managers))
            )
            event.managers.add(*managers_to_add)
        
        events.append(event)
        print(f"✓ Created event: {event.title}")
    
    return events


def create_registrations(users, events):
    """Create event registrations"""
    roles = ['PARTICIPANT', 'VOLUNTEER']
    statuses = ['PENDING_APPROVAL', 'APPROVED', 'INVITED', 'REJECTED']
    
    print(f"\nCreating event registrations...")
    registration_count = 0
    
    for event in events:
        # Random number of registrations per event
        num_registrations = random.randint(2, min(8, len(users) - 1))
        
        # Select random users (excluding creator)
        available_users = [u for u in users if u != event.creator]
        if len(available_users) < num_registrations:
            num_registrations = len(available_users)
        
        selected_users = random.sample(available_users, num_registrations)
        
        for user in selected_users:
            role = random.choice(roles)
            status = random.choice(statuses)
            
            # Check if registration already exists
            if not EventRegistration.objects.filter(user=user, event=event, role=role).exists():
                now = timezone.now()
                
                EventRegistration.objects.create(
                    user=user,
                    event=event,
                    role=role,
                    status=status,
                    requested_at=now - timedelta(days=random.randint(1, 15)),
                    invited_at=now - timedelta(days=random.randint(1, 10)) if status == 'INVITED' else None,
                    processed_at=now - timedelta(days=random.randint(0, 5)) if status in ['APPROVED', 'REJECTED'] else None
                )
                registration_count += 1
    
    print(f"✓ Created {registration_count} event registrations")
    return registration_count


def main():
    print("🎭 Event Management System - Fake Data Generator")
    print("=" * 50)
    
    try:
        # Create categories
        print("\n📂 Creating Event Categories...")
        categories = create_event_categories()
        
        # Create users
        print(f"\n👥 Creating Users...")
        users = create_users(count=15)
        
        # Create events
        print(f"\n📅 Creating Events...")
        events = create_events(users, categories, count=8)
        
        # Create registrations
        print(f"\n📝 Creating Registrations...")
        create_registrations(users, events)
        
        print("\n" + "=" * 50)
        print("✅ Fake data generation completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Categories: {EventCategory.objects.count()}")
        print(f"   - Users: {User.objects.count()}")
        print(f"   - Events: {Event.objects.count()}")
        print(f"   - Registrations: {EventRegistration.objects.count()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()