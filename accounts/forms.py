from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from .models import User
from .models import UserRole


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Username"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Password"
        })
    )


class StaffCreationForm(UserCreationForm):

    ROLE_CHOICES = [
        (UserRole.ADMIN, "Admin"),
        (UserRole.ENGINEER, "Engineer"),
    ]

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control"
        })
    )

    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control"
        })
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control"
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control"
        })
    )

    mobile_number = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "maxlength": "10"
        })
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )

    STATUS_CHOICES = (
        (True, "Active"),
        (False, "Inactive"),
    )

    is_active = forms.TypedChoiceField(
        choices=STATUS_CHOICES,
        coerce=lambda value: value == "True",
        initial=True,
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    class Meta:

        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "mobile_number",
            "role",
            "is_active",
            "password1",
            "password2",
        ]

    def clean_mobile_number(self):

        mobile = self.cleaned_data["mobile_number"]

        if not mobile.isdigit():

            raise forms.ValidationError("Mobile number must contain digits only.")

        if len(mobile) != 10:

            raise forms.ValidationError("Mobile number must contain exactly 10 digits.")

        return mobile

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")

        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:

            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class StaffUpdateForm(ModelForm):

    ROLE_CHOICES = StaffCreationForm.ROLE_CHOICES

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )

    STATUS_CHOICES = StaffCreationForm.STATUS_CHOICES

    is_active = forms.TypedChoiceField(
        choices=STATUS_CHOICES,
        coerce=lambda value: value == "True",
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )

    class Meta:

        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "mobile_number",
            "role",
            "is_active",
        ]

        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "username": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
            }),
            "mobile_number": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": "10",
            }),
        }

    def clean_mobile_number(self):

        mobile = self.cleaned_data["mobile_number"]

        if not mobile.isdigit():
            raise forms.ValidationError("Mobile number must contain digits only.")

        if len(mobile) != 10:
            raise forms.ValidationError("Mobile number must contain exactly 10 digits.")

        return mobile


class PasswordResetForm(forms.Form):

    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")

        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:

            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
