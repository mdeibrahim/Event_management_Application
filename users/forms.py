from django import forms
from tasks.models import EventRegistration

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