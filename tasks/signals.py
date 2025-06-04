from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string 
from tasks.models import EventRegistration 

@receiver(post_save, sender=EventRegistration)
def send_acceptance_email(sender, instance, created, **kwargs):
    if instance.status == 'APPROVED':
        user_to_notify = instance.user
        subject = f"Confirmation for joining '{instance.event.title}'"

        message = f"""
        Dear {user_to_notify.first_name or user_to_notify.username},

        We are very happy to inform you that your request to join '{instance.event.title}' as a '{instance.get_role_display()}' has been accepted by the Manager of the event.

        Event Details:
        Event Name: {instance.event.title}
        Your Role: {instance.get_role_display()}

        Now you can see all the details in your activity Dashboard. Inshallah, Meet you soon.

        Thank You
        {instance.event.title} Team
        """

        context = {
            'user_name': user_to_notify.first_name or user_to_notify.username,
            'event_name': instance.event.title,
            'role': instance.get_role_display(),
            'event_manager_email': instance.event.creator.email,
        }
        html_message = render_to_string('emails/event_acceptance_email.html', context)
        plain_message = render_to_string('emails/event_acceptance_email.txt', context)

        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user_to_notify.email]

        try:
            send_mail(
                subject,
                plain_message,
                from_email,
                recipient_list,
                html_message=html_message,
                fail_silently=False
            )
            print(f'A confirmation mail has been sent for the {instance.event.title} to {user_to_notify.email}')
        except Exception as e:
            print(f"Error sending mail: {e}")