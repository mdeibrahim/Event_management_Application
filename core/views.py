from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.
def public_home(request):
    return render(request, 'public_home.html')

def sign_up(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'sign_up.html')
            
        # TODO: Add user creation logic here
        messages.success(request, 'Account created successfully! Please sign in.')
        return redirect('sign_in')
        
    return render(request, 'sign_up.html')

def sign_in(request):
    return render(request, 'sign_in.html')