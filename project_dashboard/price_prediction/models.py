from django.db import models

# Create your models here.

class Cryptocurrency(models.Model):
    COIN_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('BNB', 'Binance Coin'),
    ]
    
    symbol = models.CharField(max_length=3, choices=COIN_CHOICES, unique=True)
    name = models.CharField(max_length=50)
    current_price = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class PricePrediction(models.Model):
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    predicted_price = models.DecimalField(max_digits=20, decimal_places=2)
    prediction_date = models.DateTimeField()
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-prediction_date']

    def __str__(self):
        return f"{self.cryptocurrency.symbol} Prediction: ${self.predicted_price} ({self.prediction_date})"
