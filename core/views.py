from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from .sign_up_regestration_form import RegestrationForm
from tasks.models import Profile

User = get_user_model()

# Create your views here.
def public_home(request):
    return render(request, 'public_home.html')

def sign_up(request):
    if request.method == 'POST':
        form = RegestrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a profile for the new user
            Profile.objects.create(user=user)
            messages.success(request, 'Account created successfully! Please sign in.')
            return redirect('sign_in')
    else:
        form = RegestrationForm()
    return render(request, 'sign_up.html', {'form': form})

def sign_in(request):
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
                messages.success(request, f'Welcome back, {authenticated_user.username}!')
                return redirect('user_home')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    
    return render(request, 'sign_in.html')