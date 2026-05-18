import uuid
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '2547XXXXXXXX'})
    )
    referral_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Referral code (optional)'})
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone_number',
            'password1', 'password2', 'referral_code'
        ]

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone.startswith('254'):
            raise forms.ValidationError('Phone must start with 254 e.g. 254712345678')
        if len(phone) != 12:
            raise forms.ValidationError('Enter a valid 12-digit number e.g. 254712345678')
        if not phone[3:].isdigit():
            raise forms.ValidationError('Phone number must contain digits only after 254')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if code:
            if not User.objects.filter(referral_code=code).exists():
                raise forms.ValidationError('Invalid referral code.')
        return code


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
