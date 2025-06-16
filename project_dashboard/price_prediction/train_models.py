import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import requests
import joblib
import os
from datetime import datetime, timedelta
import ta  # Technical Analysis library

def fetch_historical_data(symbol, days=365):  # Using 365 days for free API
    """Fetch historical price data from CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': str(days),
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    if not response.ok:
        raise Exception(f"Failed to fetch data from CoinGecko: {response.text}")
    
    data = response.json()
    if not data or 'prices' not in data:
        raise Exception(f"Invalid response from CoinGecko: {data}")
    
    # Extract dates, prices, and volumes
    dates = [datetime.fromtimestamp(price[0]/1000) for price in data['prices']]
    prices = [price[1] for price in data['prices']]
    volumes = [vol[1] for vol in data['total_volumes']] if 'total_volumes' in data else [0] * len(prices)
    market_caps = [cap[1] for cap in data['market_caps']] if 'market_caps' in data else [0] * len(prices)
    
    df = pd.DataFrame({
        'date': dates,
        'price': prices,
        'volume': volumes,
        'market_cap': market_caps
    })
    return df

def prepare_features(df):
    """Prepare features for the model."""
    # Create time-based features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df['day_of_year'] = df['date'].dt.dayofyear
    
    # Create lag features
    for i in range(1, 15):  # Increased lag features
        df[f'price_lag_{i}'] = df['price'].shift(i)
        df[f'volume_lag_{i}'] = df['volume'].shift(i)
    
    # Create rolling mean features
    for window in [7, 14, 30, 60]:  # Added 60-day window
        df[f'price_rolling_mean_{window}'] = df['price'].rolling(window=window).mean()
        df[f'volume_rolling_mean_{window}'] = df['volume'].rolling(window=window).mean()
        df[f'price_rolling_std_{window}'] = df['price'].rolling(window=window).std()
    
    # Add technical indicators
    df['rsi'] = ta.momentum.RSIIndicator(df['price']).rsi()
    df['macd'] = ta.trend.MACD(df['price']).macd()
    df['macd_signal'] = ta.trend.MACD(df['price']).macd_signal()
    df['bollinger_high'] = ta.volatility.BollingerBands(df['price']).bollinger_hband()
    df['bollinger_low'] = ta.volatility.BollingerBands(df['price']).bollinger_lband()
    
    # Add price changes
    df['price_change'] = df['price'].pct_change()
    df['volume_change'] = df['volume'].pct_change()
    
    # Add market cap features
    df['market_cap_change'] = df['market_cap'].pct_change()
    df['price_to_market_cap'] = df['price'] / df['market_cap']
    
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
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train multiple models
    models = {
        'random_forest': RandomForestRegressor(n_estimators=200, random_state=42),
        'gradient_boosting': GradientBoostingRegressor(n_estimators=200, random_state=42)
    }
    
    best_model = None
    best_score = float('-inf')
    
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train_scaled, y_train)
        score = model.score(X_test_scaled, y_test)
        print(f"{name} R2 score: {score:.4f}")
        
        if score > best_score:
            best_score = score
            best_model = model
    
    # Calculate model metrics
    y_pred = best_model.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\nBest model metrics:")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE: {mae:.2f}")
    print(f"R2 Score: {r2:.4f}")
    
    # Save model and scaler
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    joblib.dump(best_model, os.path.join(models_dir, f'{symbol}_model.joblib'))
    joblib.dump(scaler, os.path.join(models_dir, f'{symbol}_scaler.joblib'))
    joblib.dump(feature_columns, os.path.join(models_dir, f'{symbol}_features.joblib'))
    
    # Save model metrics
    metrics = {
        'rmse': rmse,
        'mae': mae,
        'r2': r2
    }
    joblib.dump(metrics, os.path.join(models_dir, f'{symbol}_metrics.joblib'))
    
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