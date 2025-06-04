from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
import re

User = get_user_model()

class RegestrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        
        # Remove help text
        for name in ['username', 'password1', 'password2']:
            self.fields[name].help_text = None
            
        # Add styling to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm'
            })

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError(
                "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
            )
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError(
                "Password must contain at least one Capital Letter A - Z"
            )
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError(
                "Password must contain at least one Small Letter a - z"
            )
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError(
                "Password must contain at least one number 0 - 9"
            )
        
        return password

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
