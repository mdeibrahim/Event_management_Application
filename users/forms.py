from django import forms
from tasks.models import EventRegistration, Event, EventCategory, Profile
from django.utils import timezone

class InviteUserForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    role = forms.ChoiceField(
        choices=EventRegistration.ROLE_CHOICES,
        widget=forms.HiddenInput()
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Add a personal touch to your invitation...'
        })
    ) 

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'date', 'time', 'location', 'visibility',
            'event_cover', 'max_attendees', 'tags'
        ]

class EventUpdateForm(forms.ModelForm):
    title = forms.CharField(
        label="Event Name", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    category = forms.ChoiceField(
        label="Event Category", 
        required=True,
        choices=[
            ("", "Select a category"),
            ("general", "General"),
            ("conference", "Conference"),
            ("workshop", "Workshop"),
            ("meetup", "Meetup"),
            ("webinar", "Webinar"),
            ("social", "Social Gathering"),
            ("sports", "Sports"),
            ("other", "Other"),
        ],
    )
    date = forms.DateField(
        label="Date", 
        required=True, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    time = forms.TimeField(
        label="Time", 
        required=True, 
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    location = forms.CharField(
        label="Location", 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 123 Main St, Anytown or Online'})
    )
    description = forms.CharField(
        label="Description", 
        required=True, 
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Provide a detailed description of your event...'})
    )
    event_cover = forms.ImageField(
        label="Event Cover Photo (Optional)", 
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    max_attendees = forms.IntegerField(
        label="Maximum Attendees (Optional)", 
        required=False, 
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 100 (leave blank for unlimited)'})
    )
    visibility = forms.ChoiceField(
        label="Visibility", 
        choices=Event.VISIBILITY_CHOICES, 
        required=True, 
        widget=forms.RadioSelect
    )
    tags = forms.CharField(
        label="Tags (Optional)", 
        required=False, 
        help_text="Comma-separated tags",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., tech, networking, startup (comma-separated)'})
    )

    class Meta:
        model = Event
        fields = ['title', 'date', 'time', 'location', 'description', 
                 'event_cover', 'max_attendees', 'visibility', 'tags']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Set initial values from the instance
            self.initial.update({
                'title': self.instance.title,
                'date': self.instance.date,
                'time': self.instance.time,
                'location': self.instance.location,
                'description': self.instance.description,
                'max_attendees': self.instance.max_attendees,
                'visibility': self.instance.visibility,
                'tags': self.instance.tags
            })
            # Handle category separately
            if self.instance.category:
                self.initial['category'] = self.instance.category.name.lower()
        
        self.fields['date'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('date')
        event_time = cleaned_data.get('time')

        # Validate date
        if event_date and event_date < timezone.now().date():
            if not self.instance or (self.instance and self.instance.date != event_date):
                self.add_error('date', "Event date cannot be in the past.")

        # Validate time for today's events
        if event_date and event_time:
            if event_date == timezone.now().date() and event_time < timezone.now().time():
                if not self.instance or (self.instance and (self.instance.date != event_date or self.instance.time != event_time)):
                    self.add_error('time', "For today's event, please select a future time.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle category
        category_name = self.cleaned_data.get('category')
        if category_name:
            category, _ = EventCategory.objects.get_or_create(
                name__iexact=category_name,
                defaults={'name': category_name}
            )
            instance.category = category
        else:
            instance.category = None

        if commit:
            instance.save()
        return instance

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput()
    )
    
    class Meta:
        model = Profile
        fields = ['phone_number', 'age', 'gender', 'profile_picture']
        widgets = {
            'age': forms.NumberInput(),
            'gender': forms.Select(),
            'profile_picture': forms.FileInput(),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove any non-digit characters
            phone_number = ''.join(filter(str.isdigit, phone_number))
            
            # Check if the phone number is valid (between 10 and 15 digits)
            if ( (len(phone_number)>0 and len(phone_number)<11) or len(phone_number)>11 ):
                raise forms.ValidationError('Phone number must be 11 digits')
            
            
            # Format the phone number (optional)
            if not phone_number.startswith(('013','015','016','017','018','019')):
                raise forms.ValidationError('Phone number is not valid')
            
            return phone_number
        return phone_number

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Update user's first and last name
            user = profile.user
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.save()
            profile.save()
        return profile