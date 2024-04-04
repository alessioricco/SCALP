import asyncio
import pandas as pd
from ccxt.async_support import bybit
from ta.trend import MACD
from ta.momentum import RSIIndicator
import os
import TradingStrategy
from dotenv import load_dotenv

concurrent_fetches = 5  # Adjust based on the exchange's rate limit
fetch_semaphore = asyncio.Semaphore(concurrent_fetches)

load_dotenv()
apiKey = os.getenv('BYBIT_API_KEY')
apiSecret = os.getenv('BYBIT_API_SECRET')

# Initialize exchange connection
exchange = bybit({
    'apiKey': apiKey,
    'secret': apiSecret,
})

async def run_bot(strategy):
    symbols = ["BTC/USDT", "ETH/USDT"]  # Define your symbols or dynamically load from exchange
    tasks = [process_symbol(symbol, strategy) for symbol in symbols]
    await asyncio.gather(*tasks)

async def process_symbol(symbol, strategy):
    print(f"Processing {symbol}")
    df = await safe_fetch(symbol)
    if df is not None:
        data = {
            'macd': MACD(df['close']).macd(),
            'rsi': RSIIndicator(df['close']).rsi(),
        }
        if strategy.start_condition(data):
            await start_trading(symbol)
        elif strategy.stop_condition(data):
            await stop_trading(symbol)

async def safe_fetch(symbol, attempts=3, sleep_time=5):
    async with fetch_semaphore:
        for i in range(attempts):
            try:
                candles = await exchange.fetch_ohlcv(symbol, timeframe='1d', limit=100)
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                if df.empty:
                    raise ValueError(f"No data returned for {symbol}")
                return df
            except Exception as e:
                print(f"Attempt {i+1} failed for {symbol}: {e}")
                await asyncio.sleep(sleep_time)
        raise Exception(f"Failed to fetch data for {symbol} after {attempts} attempts")

async def start_trading(symbol):
    print(f"Starting trade for {symbol}")
    # Placeholder for real trading logic

async def stop_trading(symbol):
    print(f"Stopping trade for {symbol}")
    # Placeholder for real trading logic

if __name__ == "__main__":
    # Ensure TradingStrategy module is correctly imported and used
    strategy = TradingStrategy.MACDStrategy()  # Example: Using the MACD strategy
    asyncio.run(run_bot(strategy))
