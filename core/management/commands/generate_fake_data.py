from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
import random
from datetime import datetime, timedelta
from core.models import User
from tasks.models import Profile, EventCategory, Event, EventRegistration, Notification
import uuid


class Command(BaseCommand):
    help = 'Generate fake data for the event management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to create (default: 50)'
        )
        parser.add_argument(
            '--events',
            type=int,
            default=20,
            help='Number of events to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()
        
        users_count = options['users']
        events_count = options['events']
        
        self.stdout.write(f'Generating {users_count} users and {events_count} events...')
        
        with transaction.atomic():
            # Create event categories
            categories = self.create_event_categories(fake)
            
            # Create users with profiles
            users = self.create_users_with_profiles(fake, users_count)
            
            # Create events
            events = self.create_events(fake, users, categories, events_count)
            
            # Create event registrations
            self.create_event_registrations(fake, users, events)
            
            # Create some notifications
            self.create_notifications(fake, users, events)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {users_count} users, {events_count} events, '
                f'and related data!'
            )
        )

    def clear_data(self):
        """Clear existing data (except superusers)"""
        Notification.objects.all().delete()
        EventRegistration.objects.all().delete()
        Event.objects.all().delete()
        EventCategory.objects.all().delete()
        Profile.objects.filter(user__is_superuser=False).delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write('Existing data cleared.')

    def create_event_categories(self, fake):
        """Create event categories"""
        categories_data = [
            {'name': 'Technology', 'description': 'Tech conferences, workshops, and meetups'},
            {'name': 'Business', 'description': 'Business networking and professional events'},
            {'name': 'Education', 'description': 'Educational workshops and seminars'},
            {'name': 'Sports', 'description': 'Sports events and competitions'},
            {'name': 'Arts & Culture', 'description': 'Cultural events, exhibitions, and performances'},
            {'name': 'Health & Wellness', 'description': 'Health, fitness, and wellness events'},
            {'name': 'Social', 'description': 'Social gatherings and community events'},
            {'name': 'Entertainment', 'description': 'Entertainment and leisure events'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = EventCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
        
        self.stdout.write(f'Created {len(categories)} event categories.')
        return categories

    def create_users_with_profiles(self, fake, count):
        """Create users with their profiles"""
        users = []
        roles = ['GENERAL_USER', 'EVENT_MANAGER', 'VOLUNTEER', 'PARTICIPANT']
        gender_choices = ['MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY']
        
        for i in range(count):
            # Create user
            username = fake.user_name() + str(random.randint(100, 999))
            email = fake.email()
            
            # Ensure unique username and email
            while User.objects.filter(username=username).exists():
                username = fake.user_name() + str(random.randint(100, 999))
            while User.objects.filter(email=email).exists():
                email = fake.email()
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',  # Simple password for testing
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                primary_role=random.choice(roles)
            )
            
            # Create profile for user
            Profile.objects.create(
                user=user,
                phone_number=self.generate_bd_phone(),
                age=random.randint(18, 65),
                gender=random.choice(gender_choices)
            )
            
            users.append(user)
        
        self.stdout.write(f'Created {len(users)} users with profiles.')
        return users

    def generate_bd_phone(self):
        """Generate a Bangladeshi phone number"""
        prefixes = ['013', '015', '016', '017', '018', '019']
        prefix = random.choice(prefixes)
        number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return prefix + number

    def create_events(self, fake, users, categories, count):
        """Create events"""
        events = []
        visibility_choices = ['PUBLIC', 'PRIVATE']
        
        event_titles = [
            'Tech Innovation Summit', 'Business Networking Night', 'Python Workshop',
            'Digital Marketing Masterclass', 'Startup Pitch Competition',
            'Web Development Bootcamp', 'AI & Machine Learning Conference',
            'Blockchain Technology Seminar', 'Cybersecurity Workshop',
            'Data Science Meetup', 'Mobile App Development', 'Cloud Computing Summit',
            'Software Testing Conference', 'DevOps Best Practices', 'UI/UX Design Workshop',
            'Project Management Seminar', 'Leadership Training', 'Team Building Event',
            'Cultural Festival', 'Art Exhibition', 'Music Concert', 'Dance Performance',
            'Sports Tournament', 'Fitness Challenge', 'Yoga Session', 'Health Awareness',
            'Community Service', 'Charity Fundraiser', 'Environmental Awareness',
            'Educational Seminar'
        ]
        
        for i in range(count):
            # Random future date (1 to 90 days from now)
            event_date = fake.date_between(start_date='today', end_date='+90d')
            event_time = fake.time()
            
            # Select random creator
            creator = random.choice(users)
            
            # Generate event data
            title = random.choice(event_titles) + f" {random.randint(2024, 2025)}"
            visibility = random.choice(visibility_choices)
            
            event = Event.objects.create(
                title=title,
                description=fake.text(max_nb_chars=500),
                category=random.choice(categories),
                date=event_date,
                time=event_time,
                location=fake.address(),
                creator=creator,
                visibility=visibility,
                secret_code=str(uuid.uuid4())[:8] if visibility == 'PRIVATE' else None,
                max_attendees=random.randint(10, 200) if random.choice([True, False]) else None,
                tags=', '.join(fake.words(nb=3))
            )
            
            # Add some random managers (excluding creator as they're auto-added)
            potential_managers = [u for u in users if u != creator]
            managers_to_add = random.sample(
                potential_managers, 
                min(random.randint(0, 3), len(potential_managers))
            )
            event.managers.add(*managers_to_add)
            
            events.append(event)
        
        self.stdout.write(f'Created {len(events)} events.')
        return events

    def create_event_registrations(self, fake, users, events):
        """Create event registrations"""
        registrations = []
        roles = ['PARTICIPANT', 'VOLUNTEER']
        statuses = ['PENDING_APPROVAL', 'APPROVED', 'INVITED', 'REJECTED']
        
        # Create registrations for each event
        for event in events:
            # Random number of registrations per event (3 to 15)
            num_registrations = random.randint(3, min(15, len(users) - 1))
            
            # Select random users (excluding creator)
            available_users = [u for u in users if u != event.creator]
            selected_users = random.sample(available_users, num_registrations)
            
            for user in selected_users:
                role = random.choice(roles)
                status = random.choice(statuses)
                
                # Avoid duplicate registrations
                if not EventRegistration.objects.filter(
                    user=user, event=event, role=role
                ).exists():
                    now = timezone.now()
                    
                    registration = EventRegistration.objects.create(
                        user=user,
                        event=event,
                        role=role,
                        status=status,
                        requested_at=now - timedelta(days=random.randint(1, 30)),
                        invited_at=now - timedelta(days=random.randint(1, 20)) if status == 'INVITED' else None,
                        processed_at=now - timedelta(days=random.randint(0, 10)) if status in ['APPROVED', 'REJECTED'] else None
                    )
                    registrations.append(registration)
        
        self.stdout.write(f'Created {len(registrations)} event registrations.')
        return registrations

    def create_notifications(self, fake, users, events):
        """Create sample notifications"""
        notifications = []
        notification_types = [
            'EVENT_INVITE_PARTICIPANT', 'EVENT_INVITE_VOLUNTEER', 'JOIN_REQUEST_PARTICIPANT',
            'JOIN_REQUEST_VOLUNTEER', 'REQUEST_APPROVED', 'REQUEST_REJECTED',
            'EVENT_UPDATE', 'ROLE_ASSIGNED'
        ]
        
        # Create 2-5 notifications per user
        for user in users[:30]:  # Limit to first 30 users to avoid too many notifications
            num_notifications = random.randint(2, 5)
            
            for _ in range(num_notifications):
                sender = random.choice([u for u in users if u != user])
                event = random.choice(events)
                notification_type = random.choice(notification_types)
                
                notification = Notification.objects.create(
                    recipient=user,
                    sender=sender,
                    event=event,
                    notification_type=notification_type,
                    message=f"Notification regarding {event.title}: {notification_type.replace('_', ' ').title()}",
                    is_read=random.choice([True, False]),
                    timestamp=timezone.now() - timedelta(days=random.randint(0, 30))
                )
                notifications.append(notification)
        
        self.stdout.write(f'Created {len(notifications)} notifications.')
        return notifications