import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import requests
import joblib
import os
from datetime import datetime, timedelta

def fetch_historical_data(symbol, days=365):
    """Fetch historical price data from CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': str(days),
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    data = response.json()
    # Correctly extract dates and prices
    dates = [datetime.fromtimestamp(price[0]/1000) for price in data['prices']]
    prices = [price[1] for price in data['prices']]
    df = pd.DataFrame({
        'date': dates,
        'price': prices
    })
    return df

def prepare_features(df):
    """Prepare features for the model."""
    # Create time-based features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    
    # Create lag features
    for i in range(1, 8):
        df[f'price_lag_{i}'] = df['price'].shift(i)
    
    # Create rolling mean features
    for window in [7, 14, 30]:
        df[f'price_rolling_mean_{window}'] = df['price'].rolling(window=window).mean()
    
    # Drop rows with NaN values
    df = df.dropna()
    
    # Prepare features and target
    feature_columns = [col for col in df.columns if col not in ['date', 'price']]
    X = df[feature_columns]
    y = df['price']
    
    return X, y, feature_columns

def train_model(symbol):
    """Train a model for the given cryptocurrency."""
    print(f"Training model for {symbol}...")
    
    # Fetch historical data
    df = fetch_historical_data(symbol)
    
    # Prepare features
    X, y, feature_columns = prepare_features(df)
    
    # Scale features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    # Save model and scaler
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    joblib.dump(model, os.path.join(models_dir, f'{symbol}_model.joblib'))
    joblib.dump(scaler, os.path.join(models_dir, f'{symbol}_scaler.joblib'))
    joblib.dump(feature_columns, os.path.join(models_dir, f'{symbol}_features.joblib'))
    
    print(f"Model for {symbol} saved successfully!")

def main():
    """Train models for all supported cryptocurrencies."""
    symbols = ['bitcoin', 'ethereum', 'binancecoin']
    
    for symbol in symbols:
        try:
            train_model(symbol)
        except Exception as e:
            print(f"Error training model for {symbol}: {str(e)}")

if __name__ == '__main__':
    main() 