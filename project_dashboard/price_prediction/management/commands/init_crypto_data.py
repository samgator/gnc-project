from django.core.management.base import BaseCommand
from price_prediction.models import Cryptocurrency
import requests
from datetime import datetime

class Command(BaseCommand):
    help = 'Initialize cryptocurrency data in the database'

    def handle(self, *args, **kwargs):
        # List of cryptocurrencies to initialize
        cryptos = [
            {'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin'},
            {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum'},
            {'id': 'binancecoin', 'symbol': 'BNB', 'name': 'Binance Coin'}
        ]

        # Fetch current prices from CoinGecko
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ','.join(crypto['id'] for crypto in cryptos),
            'vs_currencies': 'usd'
        }
        
        try:
            response = requests.get(url, params=params)
            prices = response.json()

            for crypto in cryptos:
                current_price = prices[crypto['id']]['usd']
                
                # Create or update cryptocurrency record
                Cryptocurrency.objects.update_or_create(
                    symbol=crypto['symbol'],
                    defaults={
                        'name': crypto['name'],
                        'current_price': current_price,
                        'last_updated': datetime.now()
                    }
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully initialized {crypto["name"]} with price ${current_price:,.2f}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing cryptocurrency data: {str(e)}')
            ) 