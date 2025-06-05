from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from .sign_up_regestration_form import RegestrationForm
from tasks.models import Profile
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os

User = get_user_model()

def generate_verification_token():
    return get_random_string(length=32)

def send_verification_email(request, user, token):
    verification_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': token})
    )
    subject = 'Verify your email address'
    
    # Create email template directory if it doesn't exist
    template_dir = os.path.join(settings.BASE_DIR, 'core', 'templates', 'core', 'email')
    os.makedirs(template_dir, exist_ok=True)
    
    html_message = render_to_string('core/email/verification_email.html', {
        'user': user,
        'verification_url': verification_url
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

# Create your views here.
def public_home(request):
    return render(request, 'public_home.html')

def sign_up(request):
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect('user_home')
    
    if request.method == 'POST':
        form = RegestrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User is inactive until email is verified
            user.save()
            
            # Create a profile for the new user
            Profile.objects.create(user=user)
            
            # Generate and save verification token
            token = generate_verification_token()
            user.profile.email_verification_token = token
            user.profile.save()
            
            # Send verification email
            send_verification_email(request, user, token)
            
            messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            return redirect('sign_in')
    else:
        form = RegestrationForm()
    return render(request, 'sign_up.html', {'form': form})

def verify_email(request, token):
    try:
        profile = Profile.objects.get(email_verification_token=token)
        user = profile.user
        user.is_active = True
        user.save()
        profile.email_verification_token = None
        profile.save()
        messages.success(request, 'Email verified successfully! You can now sign in.')
        return redirect('sign_in')
    except Profile.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('sign_in')

def sign_in(request):
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect('user_home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # First get the user by email
            user = User.objects.get(email=email)
            # Then authenticate with username and password
            authenticated_user = authenticate(request, username=user.username, password=password)
            
            if authenticated_user is not None:
                login(request, authenticated_user)
                # Check superuser status after successful login
                # if authenticated_user.is_superuser:
                #     return redirect('admin_home')
                messages.success(request, f'Welcome back, {authenticated_user.username}!')
                return redirect('user_home')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    
    return render(request, 'sign_in.html')

@login_required
def sign_out(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('public_home')

