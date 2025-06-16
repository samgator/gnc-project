from django.shortcuts import render
from django.http import JsonResponse
from .models import Cryptocurrency, PricePrediction
from .forms import CryptocurrencySelectForm
import requests
from datetime import datetime, timedelta
from django.utils import timezone
import joblib
import os
from django.conf import settings
import pandas as pd
import numpy as np

# CoinGecko API IDs mapping
COINGECKO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'BNB': 'binancecoin'
}

def index(request):
    """Render the main page with cryptocurrency selection form."""
    form = CryptocurrencySelectForm()
    return render(request, 'price_prediction/index.html', {'form': form})

def get_prediction_data(request):
    """Get prediction data for the selected cryptocurrency."""
    try:
        symbol = request.GET.get('cryptocurrency')
        if not symbol:
            return JsonResponse({'error': 'No cryptocurrency selected'})

        # Get CoinGecko ID for the symbol
        coingecko_id = COINGECKO_IDS.get(symbol)
        if not coingecko_id:
            return JsonResponse({'error': f'Invalid cryptocurrency symbol: {symbol}'})

        # Fetch current price from CoinGecko
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coingecko_id,
            'vs_currencies': 'usd'
        }
        response = requests.get(url, params=params)
        if not response.ok:
            return JsonResponse({'error': f'Failed to fetch price data: {response.text}'})
        
        current_price = response.json()[coingecko_id]['usd']

        # Update or create cryptocurrency record
        crypto, created = Cryptocurrency.objects.get_or_create(
            symbol=symbol,
            defaults={
                'name': symbol.capitalize(),
                'current_price': current_price,
                'last_updated': timezone.now()
            }
        )
        if not created:
            crypto.current_price = current_price
            crypto.last_updated = timezone.now()
            crypto.save()

        # Load model and make predictions
        if symbol == 'BTC':
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            model = joblib.load(os.path.join(models_dir, 'bitcoin_model.joblib'))
            scaler = joblib.load(os.path.join(models_dir, 'bitcoin_scaler.joblib'))
            feature_columns = joblib.load(os.path.join(models_dir, 'bitcoin_features.joblib'))
        elif symbol == 'ETH':
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            model = joblib.load(os.path.join(models_dir, 'ethereum_model.joblib'))
            scaler = joblib.load(os.path.join(models_dir, 'ethereum_scaler.joblib'))
            feature_columns = joblib.load(os.path.join(models_dir, 'ethereum_features.joblib'))
        elif symbol == 'BNB':
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            model = joblib.load(os.path.join(models_dir, 'binancecoin_model.joblib'))
            scaler = joblib.load(os.path.join(models_dir, 'binancecoin_scaler.joblib'))
            feature_columns = joblib.load(os.path.join(models_dir, 'binancecoin_features.joblib'))
        else:
            return JsonResponse({'error': f'Invalid cryptocurrency symbol: {symbol}'})

        # Prepare features for prediction
        last_date = timezone.now()
        dates = [last_date + timedelta(days=i) for i in range(1, 31)]
        
        # Create DataFrame with future dates
        future_df = pd.DataFrame({
            'date': dates,
            'price': [current_price] * 30  # Use current price as initial value
        })

        # Add time-based features
        future_df['day_of_week'] = future_df['date'].dt.dayofweek
        future_df['month'] = future_df['date'].dt.month
        future_df['year'] = future_df['date'].dt.year

        # Add lag features (using current price for initial lags)
        for i in range(1, 8):
            future_df[f'price_lag_{i}'] = future_df['price'].shift(i).fillna(current_price)

        # Add rolling mean features
        for window in [7, 14, 30]:
            future_df[f'price_rolling_mean_{window}'] = future_df['price'].rolling(window=window).mean().fillna(current_price)

        # Prepare features for prediction
        X = future_df[feature_columns]
        X_scaled = scaler.transform(X)

        # Make predictions
        predictions = model.predict(X_scaled)

        # Save predictions to database
        for date, pred_price in zip(dates, predictions):
            PricePrediction.objects.create(
                cryptocurrency=crypto,
                predicted_price=pred_price,
                prediction_date=date,
                confidence_score=0.85,  # Example confidence score
                created_at=timezone.now()
            )

        # Prepare response data
        response_data = {
            'symbol': symbol.upper(),
            'current_price': current_price,
            'dates': [date.strftime('%Y-%m-%d') for date in dates],
            'predictions': predictions.tolist(),
            'price_change': ((predictions[0] - current_price) / current_price) * 100  # Calculate percentage change
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)})
