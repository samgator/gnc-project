from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'member_name', 'password1', 'password2')

class TokenTransferForm(forms.Form):
    to_address = forms.CharField(
        label='Recipient Address',
        max_length=42,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0x...'
        })
    )
    amount = forms.DecimalField(
        label='Amount',
        max_digits=18,
        decimal_places=6,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.0'
        })
    ) 
