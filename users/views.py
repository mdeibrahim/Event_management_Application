from django.shortcuts import render

# Create your views here.

def admin_dashboard(request):
    return render(request, 'admin/admin_home.html')

def user_home(request):
    return render(request, 'user_home.html')

def manager_dashboard(request):
    return render(request, 'manager_dashboard.html')

def user_activity(request):
    return render(request, 'user_activity.html')

def add_an_event(request):
    return render(request, 'add_an_event.html')

def manage_spacific_event(request):
    return render(request, 'manage_spacific_event.html')
