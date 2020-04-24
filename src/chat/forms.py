from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm                                    
from django.contrib.auth.models import User

from .models import UserProfile


class ComposeForm(forms.Form):
    message = forms.CharField(
            strip=True,
            widget=forms.TextInput(
                attrs={"class": "form-control",
                       'placeholder': 'Enter your message here'}
            ))


class UserSearchForm(forms.Form):
    username_search = forms.CharField(
        strip=True,
        widget=forms.TextInput(
                attrs={"id": "searchBox",
                       "class": "form-control wide-input",
                       'placeholder': 'Type in the user to chat with here'}
                )
    )


class UserProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image']
        labels = {
            'profile_image': _('Profile Image'),
        }
        help_texts = {
            'profile_image': _('Upload your profile image here.'),
        }


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        )

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class EditUserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'password'
        )
