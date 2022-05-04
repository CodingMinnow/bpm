from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True, min_length=2, max_length=50)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ("username","first_name","email",)

class CustomUserChangeForm(UserChangeForm):
    first_name = forms.CharField(required=True, min_length=2, max_length=50)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ("username","first_name","email",)
