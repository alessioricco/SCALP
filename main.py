import asyncio
import pandas as pd
import ccxt.async_support 
# from ta.trend import MACD
# from ta.momentum import RSIIndicator, StochRSIIndicator
import os
# import TradingStrategy
from dotenv import load_dotenv
import datetime

from StateMachines.MACDStateMachine import MACDStateMachine
from StateMachines.StochasticRSIStateMachine import StochasticRSIStateMachine
from StateMachines.TradingStateMachine import TradingStateMachine
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from Strategies.MacdStochTradingStrategy import MacdStochRSITradingStrategy
import json
from rich.console import Console
console = Console()

concurrent_fetches = 5  # Adjust based on the exchange's rate limit
fetch_semaphore = asyncio.Semaphore(concurrent_fetches)
process_semaphore = asyncio.Semaphore(1)

load_dotenv()
apiKey = os.getenv('BYBIT_API_KEY')
apiSecret = os.getenv('BYBIT_API_SECRET')

print(ccxt.exchanges)

# Initialize exchange connection
exchange = ccxt.bybit({
    'apiKey': apiKey,
    'secret': apiSecret,
})
exchange.set_sandbox_mode(True)

# Read blacklist from file
blacklist = []
with open('blacklist.json', 'r') as file:
    blacklist = json.load(file)

max_candles_to_fetch = 100
max_candles_to_check = 20
timeframes = ['1m']#, '15m', '1h', '4h', '1d']

def build_trader(symbol:str=""):
    macd_sm = MACDStateMachine()
    stochastic_sm = StochasticRSIStateMachine()
    strategy:AbstractTradingStrategy = MacdStochRSITradingStrategy(symbol, macd_sm, stochastic_sm)    
    trader:TradingStateMachine = TradingStateMachine(strategy)
    return trader

async def run_bot():

    symbols_list = exchange.load_markets()
    traders_pool = {}

    def traders_pool_factory(key):
        if key in traders_pool:
            return traders_pool[key]
        traders_pool[key] = build_trader(key)
        return traders_pool[key]

    while True:
    
        for timeframe in timeframes:

            try:
                if 'm' in timeframe:
                    symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('swap', False)}
                elif 'h' in timeframe:
                    symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('swap', False)}
                elif 'd' in timeframe:
                    symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('spot', False)}
                elif 'w' in timeframe:
                    symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('spot', False)}
                
                symbols = list(symbols_list.keys())
                
                # remove symbols in the form of SOL/USDC:xxxx
                symbols = [symbol for symbol in symbols if symbol not in blacklist]
                
                symbols = ['CELO/USDT:USDT']
                
                # Process symbols in groups
                group_size = 10
                for i in range(0, len(symbols), group_size):
                    
                    symbol_group = symbols[i:i+group_size]
                    tasks = [process_symbol(symbol, traders_pool_factory(f"{symbol} {timeframe}"), timeframe=timeframe) for symbol in symbol_group]
                    await asyncio.gather(*tasks)
            
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error occurred: {e}")
            
    print("done")

async def fetch_data(symbol, attempts=1, sleep_time=1, timeframe='1d'):
    async with fetch_semaphore:
        for i in range(attempts):
            try:
                limit = max_candles_to_fetch
                candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                if df.empty:
                    raise ValueError(f"No data returned for {symbol}")
                if len(df) < limit:
                    raise ValueError(f"Insufficient data returned for {symbol}")
                return df
            except Exception as e:
                print(f"Attempt {i+1} failed for {symbol}: {e}")
                await asyncio.sleep(sleep_time)
        # raise Exception(f"Failed to fetch data for {symbol} after {attempts} attempts")

async def process_symbol(symbol, trader:TradingStateMachine, timeframe='1d'):
    # print(f"Processing {symbol}")

    df:pd.DataFrame = await fetch_data(symbol, timeframe=timeframe)
    if df is None:
        blacklist.append(symbol)
        print(f"Blacklisted {symbol}")
        return
    
    last_row = df.iloc[-1]
    if last_row.isnull().any():
        print(f"skip {symbol}")
        return

    trader.strategy.enrich_dataset(df)
    trader.enrich_dataset(df)
    # reducing the size
    df:pd.DataFrame = df.head(-1).tail(max_candles_to_check)
    
    async with process_semaphore:
        
        old_state = trader.state
        trader.process(df)
        
        if old_state != trader.state:    
            now = datetime.datetime.now(datetime.UTC)
            console.print(f"[bold]{now}[/bold] | {symbol} | [bold green]{trader.state}[/bold green]")
            print()



if __name__ == "__main__":
    
    asyncio.run(run_bot())
    