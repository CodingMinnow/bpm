from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm, SetPasswordForm

from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=False, min_length=2, max_length=30, help_text="Optional")
    email = forms.EmailField(required=True, max_length=254, help_text='Enter a valid email address')

    class Meta:
        model = CustomUser
        fields = ("username","first_name","email",)

class CustomUserChangeForm(UserChangeForm):
    first_name = forms.CharField(required=False, min_length=2, max_length=30, help_text="Optional")
    email = forms.EmailField(required=True, max_length=254, help_text='Enter a valid email address')

    class Meta:
        model = CustomUser
        fields = ("username","first_name","email",)
