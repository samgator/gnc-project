from django import forms
from .models import Cryptocurrency

class CryptocurrencySelectForm(forms.Form):
    cryptocurrency = forms.ChoiceField(
        choices=[
            ('BTC', 'Bitcoin'),
            ('ETH', 'Ethereum'),
            ('BNB', 'Binance Coin'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    ) 