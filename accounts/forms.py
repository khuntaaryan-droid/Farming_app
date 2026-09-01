from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone', 'address', 'village_or_city', 'state')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['role'].widget.attrs.update({'class': 'form-select'})

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'village_or_city', 'state')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class RoleAuthenticationForm(AuthenticationForm):
    login_role = forms.CharField(widget=forms.HiddenInput(), required=False, initial='buyer')

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        role = self.cleaned_data.get('login_role', 'buyer')
        
        if role == 'farmer' and user.role != 'FARMER':
            raise ValidationError("This account is not registered as a Farmer. Please login from the Customer tab.", code='invalid_login')
        elif role == 'agro' and user.role != 'AGRO_DEALER':
            raise ValidationError("This account is not registered as an Agro Dealer. Please login from the correct tab.", code='invalid_login')
        elif role == 'buyer' and user.role == 'FARMER':
            raise ValidationError("This account is registered as a Farmer. Please login from the Farmer tab.", code='invalid_login')
        elif role == 'buyer' and user.role == 'AGRO_DEALER':
            raise ValidationError("This account is registered as an Agro Dealer. Please login from the Agro Dealer tab.", code='invalid_login')
