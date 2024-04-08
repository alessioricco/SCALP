import asyncio
from typing import Callable
import pandas as pd
import ccxt.async_support 
import os
from dotenv import load_dotenv
import datetime

from StateMachines.TradingStateMachine import TradingStateMachine
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
import json
from rich.console import Console

from StrategyBuilders import getStrategyBuilder
console = Console()

concurrent_fetches = 5  # Adjust based on the exchange's rate limit
fetch_semaphore = asyncio.Semaphore(concurrent_fetches)
process_semaphore = asyncio.Semaphore(1)
max_candles_to_fetch = 1000
max_candles_to_check = 1000
timeframes = ['1m']#, '15m', '1h', '4h', '1d']
no_last_candle = True
BUILD_DATASET_COLLECTION=False

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

def build_trader(strategy_builder_func: Callable[[str], AbstractTradingStrategy], symbolAndTimeframe: str = "")->dict:
    trader: TradingStateMachine = TradingStateMachine(strategy_builder_func(symbolAndTimeframe))
    return {
        "trader": trader,
        "datetime": datetime.datetime.now(datetime.UTC),
        "symbol": symbolAndTimeframe 
    }

async def run_bot():

    symbols_list = exchange.load_markets()
    traders_pool = {}

    strategy_builder = getStrategyBuilder('SIMPLE')

    def traders_pool_factory(strategy_builder, key):
        """
        Factory function that creates and returns a trader from the traders_pool dictionary.
        If the trader with the given key already exists in the traders_pool, it is returned.
        Otherwise, a new trader is created using the strategy_builder and added to the traders_pool.

        Parameters:
        - strategy_builder (function): A function that builds a trading strategy.
        - key (str): The key to identify the trader in the traders_pool.

        Returns:
        - trader: The trader object from the traders_pool.

        """
        if key in traders_pool:
            return traders_pool[key]
        traders_pool[key] = build_trader(strategy_builder, key)
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
                
                symbols = ['ETH/USDT:USDT']
                
                # Process symbols in groups
                group_size = 10
                for i in range(0, len(symbols), group_size):
                    
                    symbol_group = symbols[i:i+group_size]
                    tasks = [process_symbol(symbol, traders_pool_factory(strategy_builder,f"{symbol} {timeframe}"), timeframe=timeframe) for symbol in symbol_group]
                    await asyncio.gather(*tasks)
            
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error occurred: {e}")
            
    print("done")

async def fetch_data(symbol, attempts=1, sleep_time=1, timeframe='1d'):
    """
    Fetches OHLCV data for a given symbol from an exchange.

    Args:
        symbol (str): The symbol to fetch data for.
        attempts (int, optional): The number of attempts to fetch data. Defaults to 1.
        sleep_time (int, optional): The sleep time between attempts in seconds. Defaults to 1.
        timeframe (str, optional): The timeframe of the OHLCV data. Defaults to '1d'.

    Returns:
        pandas.DataFrame: A DataFrame containing the fetched OHLCV data.

    Raises:
        ValueError: If no data is returned for the symbol.
        ValueError: If insufficient data is returned for the symbol.
    """
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

async def process_symbol(symbol, trader_info:dict, timeframe='1d')->None:
    """
    Process a symbol using a trading state machine.

    Args:
        symbol (str): The symbol to process.
        trader (TradingStateMachine): The trading state machine object.
        timeframe (str, optional): The timeframe for fetching data. Defaults to '1d'.

    Returns:
        None
    """
    # print(f"Processing {symbol}")

    trader:TradingStateMachine = trader_info['trader']

    df:pd.DataFrame = await fetch_data(symbol, timeframe=timeframe)
    if df is None:
        blacklist.append(symbol)
        print(f"Blacklisted {symbol}")
        return
    
    last_row = df.iloc[-1]
    if last_row.isnull().any():
        print(f"skip {symbol}")
        return

    trader_info["datetime"] = datetime.datetime.now(datetime.UTC)
    
    trader.strategy.enrich_dataset(df)
    trader.enrich_dataset(df)
    # reducing the size
    if no_last_candle:
        sample_df:pd.DataFrame = df.head(-1).tail(max_candles_to_check)
    else:
        sample_df:pd.DataFrame = df.tail(max_candles_to_check)
        
    async with process_semaphore:
        
        old_state = trader.state
        trader.process(sample_df)
        
        if BUILD_DATASET_COLLECTION:
            sample_df.to_csv(f"./Data/bybit/{symbol.replace('/','-')}_{timeframe}.csv")
            print(f"Saved {symbol} {timeframe} data")
        else:
            if old_state != trader.state:    
                now = datetime.datetime.now(datetime.UTC)
                
                last_close = df['close'].iloc[-1]
                color = "yellow"
                if 'buy' in trader.state:
                    color = 'green'
                elif 'sell' in trader.state:
                    color = 'red'
                    # Do something with last_close
                
                console.print(f"[bold]{now}[/bold] | {trader.strategy.getSymbolAndTimeFrame()} | [bold {color}]{trader.state}[/bold {color}] | [bold]{last_close}[/bold]")
                print()



if __name__ == "__main__":
    
    asyncio.run(run_bot())
    