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
import ta

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

        # Fetch current price and market data from CoinGecko
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coingecko_id,
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true'
        }
        response = requests.get(url, params=params)
        if not response.ok:
            return JsonResponse({'error': f'Failed to fetch price data: {response.text}'})
        
        data = response.json()[coingecko_id]
        current_price = data['usd']
        current_volume = data.get('usd_24h_vol', 0)
        current_market_cap = data.get('usd_market_cap', 0)

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
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        model = joblib.load(os.path.join(models_dir, f'{coingecko_id}_model.joblib'))
        scaler = joblib.load(os.path.join(models_dir, f'{coingecko_id}_scaler.joblib'))
        feature_columns = joblib.load(os.path.join(models_dir, f'{coingecko_id}_features.joblib'))
        metrics = joblib.load(os.path.join(models_dir, f'{coingecko_id}_metrics.joblib'))

        # Prepare features for prediction
        last_date = timezone.now()
        dates = [last_date + timedelta(days=i) for i in range(1, 31)]
        
        # Create DataFrame with future dates
        future_df = pd.DataFrame({
            'date': dates,
            'price': [current_price] * 30,
            'volume': [current_volume] * 30,
            'market_cap': [current_market_cap] * 30
        })

        # Add time-based features
        future_df['day_of_week'] = future_df['date'].dt.dayofweek
        future_df['month'] = future_df['date'].dt.month
        future_df['year'] = future_df['date'].dt.year
        future_df['day_of_year'] = future_df['date'].dt.dayofyear

        # Add lag features
        for i in range(1, 15):
            future_df[f'price_lag_{i}'] = future_df['price'].shift(i).fillna(current_price)
            future_df[f'volume_lag_{i}'] = future_df['volume'].shift(i).fillna(current_volume)

        # Add rolling mean features
        for window in [7, 14, 30, 60]:
            future_df[f'price_rolling_mean_{window}'] = future_df['price'].rolling(window=window).mean().fillna(current_price)
            future_df[f'volume_rolling_mean_{window}'] = future_df['volume'].rolling(window=window).mean().fillna(current_volume)
            future_df[f'price_rolling_std_{window}'] = future_df['price'].rolling(window=window).std().fillna(0)

        # Add technical indicators
        future_df['rsi'] = ta.momentum.RSIIndicator(future_df['price']).rsi().fillna(50)
        future_df['macd'] = ta.trend.MACD(future_df['price']).macd().fillna(0)
        future_df['macd_signal'] = ta.trend.MACD(future_df['price']).macd_signal().fillna(0)
        future_df['bollinger_high'] = ta.volatility.BollingerBands(future_df['price']).bollinger_hband().fillna(current_price)
        future_df['bollinger_low'] = ta.volatility.BollingerBands(future_df['price']).bollinger_lband().fillna(current_price)

        # Add price changes
        future_df['price_change'] = future_df['price'].pct_change().fillna(0)
        future_df['volume_change'] = future_df['volume'].pct_change().fillna(0)

        # Add market cap features
        future_df['market_cap_change'] = future_df['market_cap'].pct_change().fillna(0)
        future_df['price_to_market_cap'] = future_df['price'] / future_df['market_cap']

        # Prepare features for prediction
        X = future_df[feature_columns]
        X_scaled = scaler.transform(X)

        # Make predictions
        predictions = model.predict(X_scaled)

        # Calculate confidence intervals based on model metrics
        confidence_interval = 1.96 * metrics['rmse']  # 95% confidence interval
        upper_bound = predictions + confidence_interval
        lower_bound = predictions - confidence_interval

        # Calculate confidence scores (higher for predictions closer to current price)
        confidence_scores = 1 - (np.abs(predictions - current_price) / current_price)
        confidence_scores = np.clip(confidence_scores, 0.1, 0.95)  # Clip between 0.1 and 0.95

        # Save predictions to database
        for date, pred_price, conf_score in zip(dates, predictions, confidence_scores):
            PricePrediction.objects.create(
                cryptocurrency=crypto,
                predicted_price=pred_price,
                prediction_date=date,
                confidence_score=conf_score,
                created_at=timezone.now()
            )

        # Prepare response data
        response_data = {
            'symbol': symbol.upper(),
            'current_price': current_price,
            'dates': [date.strftime('%Y-%m-%d') for date in dates],
            'predictions': predictions.tolist(),
            'upper_bound': upper_bound.tolist(),
            'lower_bound': lower_bound.tolist(),
            'confidence_scores': confidence_scores.tolist(),
            'price_change': ((predictions[0] - current_price) / current_price) * 100,
            'model_metrics': {
                'rmse': metrics['rmse'],
                'mae': metrics['mae'],
                'r2': metrics['r2']
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)})
