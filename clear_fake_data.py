#!/usr/bin/env python3
"""
Clear fake data script for the Event Management System.
This will remove all generated fake data but keep superuser accounts.
"""

import os
import sys
import django

# Setup Django
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_management_project.settings')
django.setup()

# Import models
from core.models import User
from tasks.models import Profile, EventCategory, Event, EventRegistration, Notification


def clear_fake_data():
    """Clear all fake data but keep superuser accounts"""
    print("🧹 Clearing fake data...")
    print("⚠️  This will remove all non-superuser data!")
    
    try:
        # Count before deletion
        user_count = User.objects.filter(is_superuser=False).count()
        profile_count = Profile.objects.filter(user__is_superuser=False).count()
        event_count = Event.objects.count()
        registration_count = EventRegistration.objects.count()
        notification_count = Notification.objects.count()
        category_count = EventCategory.objects.count()
        
        print(f"\nData to be deleted:")
        print(f"   - Users (non-superuser): {user_count}")
        print(f"   - Profiles (non-superuser): {profile_count}")
        print(f"   - Events: {event_count}")
        print(f"   - Registrations: {registration_count}")
        print(f"   - Notifications: {notification_count}")
        print(f"   - Categories: {category_count}")
        
        # Ask for confirmation
        confirm = input("\nAre you sure you want to delete this data? (yes/no): ").lower().strip()
        
        if confirm == 'yes':
            # Delete in correct order (foreign key constraints)
            Notification.objects.all().delete()
            EventRegistration.objects.all().delete()
            Event.objects.all().delete()
            EventCategory.objects.all().delete()
            Profile.objects.filter(user__is_superuser=False).delete()
            User.objects.filter(is_superuser=False).delete()
            
            print("\n✅ All fake data has been cleared successfully!")
            
            # Show remaining data
            remaining_users = User.objects.count()
            print(f"\nRemaining data:")
            print(f"   - Users (superuser only): {remaining_users}")
            print(f"   - Events: {Event.objects.count()}")
            print(f"   - Categories: {EventCategory.objects.count()}")
        else:
            print("\n❌ Operation cancelled.")
    
    except Exception as e:
        print(f"\n❌ Error clearing data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    clear_fake_data()