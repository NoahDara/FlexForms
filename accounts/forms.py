from django import forms
from django.contrib.auth.models import  Group
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser as User

class CustomUserCreationForm(UserCreationForm):
    # group = forms.ModelChoiceField(queryset=Group.objects.all())

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email", "first_name", "last_name",)
        exclude = ("group",)

    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     group = self.cleaned_data.get("group")
    #     if commit:
    #         if not user.pk:
    #             user.save() 
    #         if group:
    #             group.user_set.add(user)
    #     return user


class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
        )
        exclude = ["password"]

    def __init__(self, *args, **kwargs):
        super(CustomUserUpdateForm, self).__init__(*args, **kwargs)

class LoginForm(forms.Form):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)