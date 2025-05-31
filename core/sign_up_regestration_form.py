from django.contrib.auth.forms import UserCreationForm
from tasks.models import User

class RegestrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

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
