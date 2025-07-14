from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create default user groups for the application'

    def handle(self, *args, **options):
        groups = ['Admin', 'Manager', 'General User']
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created group "{group_name}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Group "{group_name}" already exists')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Group setup completed!')
        )
