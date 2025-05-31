from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def admin_dashboard(request):
    return render(request, 'admin/admin_home.html')

@login_required
def user_home(request):
    return render(request, 'user_home.html')

@login_required
def manager_dashboard(request):
    return render(request, 'manager_dashboard.html')

@login_required
def user_activity(request):
    return render(request, 'user_activity.html')

@login_required
def add_an_event(request):
    return render(request, 'add_an_event.html')

@login_required
def manage_spacific_event(request):
    return render(request, 'manage_spacific_event.html')
