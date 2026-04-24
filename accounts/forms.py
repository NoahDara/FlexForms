from django import forms
from django.contrib.auth.models import  Group
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser as User
from helpers.forms import CustomBaseForm

class CustomUserCreationForm(CustomBaseForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email", "first_name", "last_name", "groups")
        exclude = ["password"]


class LoginForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    

from django.contrib.auth.models import Group

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Group name'})
        }