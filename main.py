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


from abc import ABC, abstractmethod

from StrategyBuilders import getStrategyBuilder
console = Console()

# concurrent_fetches = 5  # Adjust based on the exchange's rate limit
# fetch_semaphore = asyncio.Semaphore(concurrent_fetches)
# process_semaphore = asyncio.Semaphore(1)
# max_candles_to_fetch = 1000
# max_candles_to_check = 1000
# timeframes = ['1m']#, '15m', '1h', '4h', '1d']
# no_last_candle = False
BUILD_DATASET_COLLECTION=False

# load_dotenv()
# apiKey = os.getenv('BYBIT_API_KEY')
# apiSecret = os.getenv('BYBIT_API_SECRET')

# print(ccxt.exchanges)

# Initialize exchange connection
# exchange = ccxt.bybit({
#     'apiKey': apiKey,
#     'secret': apiSecret,
# })
# exchange.set_sandbox_mode(True)

# Read blacklist from file
# blacklist = []
# with open('blacklist.json', 'r') as file:
#     blacklist = json.load(file)

class ExchangeManagement(ABC):
       
    def __init__(self):
        self.sleep_time = 0.5
        self.blacklist:set = set()
    
    # @abstractmethod
    # async def fetch_data(self,symbol, attempts=1, sleep_time=1, timeframe='1d'):
    #     pass

    @staticmethod
    def getOLHCVColumnNames():
        return['timestamp', 'open', 'high', 'low', 'close', 'volume']

    @abstractmethod
    def getSymbolList(self):
        pass

    @abstractmethod
    def getExchangeName(self):
        pass

    @abstractmethod
    def readBlackList(self):
        pass
    
    @abstractmethod          
    def getBlackList(self)->set:
        pass
    
    @abstractmethod
    def appendToBlackList(self, symbol):
        pass
    
    @abstractmethod
    def getTimeFrames(self):
        pass
    
    @abstractmethod
    def get_ohlcv_Data(self, symbol:str, timeframe:str, max_candles_to_fetch:int=1000):
        pass
    
    @abstractmethod
    def getMaxCandlesToFetch(self):
        pass
    
    @abstractmethod
    def getMaxCandlesToCheck(self):
        pass
    
class ByBit(ExchangeManagement):
    def __init__(self):
        
        load_dotenv()
        apiKey = os.getenv('BYBIT_API_KEY')
        apiSecret = os.getenv('BYBIT_API_SECRET')            
        
        self.exchange = ccxt.bybit({
            'apiKey': apiKey,
            'secret': apiSecret,
        })
        self.exchange.set_sandbox_mode(True)
   
        self.readBlackList()
        super().__init__()

    def getExchangeName(self):
        return "ByBit"

    def readBlackList(self)->set:
        with open('blacklist.json', 'r') as file:
            self.blacklist = set(json.load(file))
        # return self.blacklist

    def getBlackList(self)->set:
        return self.blacklist

    def appendToBlackList(self, symbol):
        self.blacklist.add(symbol)
        with open('blacklist.json', 'w') as file:
            json.dump(list(self.blacklist), file)
            
    def getSymbolList(self):
        return self.exchange.load_markets()

    def getTimeFrames(self):
        return ['1m']#, '15m', '1h', '4h', '1d']
    
    def get_ohlcv_Data(self, symbol:str, timeframe:str, max_candles_to_fetch:int=1000):
        candles = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=max_candles_to_fetch)
        df = pd.DataFrame(candles, columns=ExchangeManagement.getOLHCVColumnNames())
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def getMaxCandlesToFetch(self):
        return 1000
    
    def getMaxCandlesToCheck(self):
        return 1000

class BackTesting(ExchangeManagement):
    def __init__(self):
        super().__init__()
        folder = "./Data/gemini"
        file = "gemini_1m.csv"
        print(f"Reading backtest data from {folder}/{file}")
        df_backtest = pd.read_csv(f"{folder}/{file}")
        self.df_backtest = df_backtest[ExchangeManagement.getOLHCVColumnNames()][200:]
        self.counter_backtest = 0
        self.sleep_time = 0.1
        
    def getExchangeName(self):
        return "BackTesting"

    def getSymbolList(self):
        # return {"symbol":"BTC/USD", "info":{"swap":False}}
        return {
                    'BTC/USDT': {
                        'swap': True,
                        'spot': False
                    }
                }
    def readBlackList(self):
        pass
    
    def getBlackList(self)->set:
        return self.blacklist

    def appendToBlackList(self, symbol):
        pass
    
    def getTimeFrames(self):
        return ['1m']#, '15m', '1h', '4h', '1d']

    def get_ohlcv_Data(self, symbol:str, timeframe:str, max_candles_to_fetch:int=1000):

        try:
            # global counter_backtest
            self.counter_backtest += 1
            
            df_backtest_slice = self.df_backtest[self.counter_backtest:self.counter_backtest+max_candles_to_fetch].copy()
            return df_backtest_slice.reset_index()
            
        except Exception as e:
            print(f"End of backtest data for {symbol}")
            return None

    def getMaxCandlesToFetch(self):
        return 1000
    
    def getMaxCandlesToCheck(self):
        return 250

class TradingSystem:

    def __init__(self, exchange:ExchangeManagement, strategy_name="SIMPLE", no_last_candle:bool = False  ) -> None:
        self.exchange = exchange
        self.strategy_name = strategy_name
        self.traders_pool:dict = {}
        self.strategy_builder:AbstractTradingStrategy = getStrategyBuilder(self.strategy_name)
        self.no_last_candle = no_last_candle
        self.getDataFrame = self._getDataFrameRule()
        concurrent_fetches = 5  # Adjust based on the exchange's rate limit
        self.fetch_semaphore = asyncio.Semaphore(concurrent_fetches)
        self.process_semaphore = asyncio.Semaphore(1)
        self.process_group_number = 10
        pass

    def _getDataFrameRule(self):
        max_candles_to_check:bool = self.exchange.getMaxCandlesToCheck()
        def getCandles(df:pd.DataFrame)->pd.DataFrame:
            return df.tail(max_candles_to_check)
        def getCandlesNoLastOne(df:pd.DataFrame)->pd.DataFrame:
            return df.head(-1).tail(max_candles_to_check)
        return getCandlesNoLastOne if self.no_last_candle else getCandles

    def _build_trader(self,strategy_builder_func: Callable[[str], AbstractTradingStrategy], symbolAndTimeframe: str = "")->dict:
            trader: TradingStateMachine = TradingStateMachine(strategy_builder_func(symbolAndTimeframe))
            return {
                "trader": trader,
                "datetime": datetime.datetime.now(datetime.UTC),
                "symbol": symbolAndTimeframe 
            }

    def _traders_pool_factory(self, key):
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
        if key in self.traders_pool:
            return self.traders_pool[key]
        self.traders_pool[key] = self._build_trader(self.strategy_builder, key)
        return self.traders_pool[key]

    def _getSymbolsForTimeframe(self, timeframe):
        
        symbols_list:list = self.exchange.getSymbolList()
        # for timeframe in self.exchange.getTimeFrames():
        try:
            if 'm' in timeframe:
                symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('swap', False)}
            elif 'h' in timeframe:
                symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('swap', False)}
            elif 'd' in timeframe:
                symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('spot', False)}
            elif 'w' in timeframe:
                symbols_list = {symbol: info for symbol, info in symbols_list.items() if info.get('spot', False)}
        except Exception as e:  
            print(f"Error occurred: {e}")
 
        symbols = list(symbols_list.keys())
        symbols = [symbol for symbol in symbols if symbol not in self.exchange.getBlackList()]  
        
        return symbols  

    async def run(self):

        # timeframes = self.exchange.getTimeFrames()
        # symbols = []
        # for timeframe in timeframes:
        #     symbols.extend(self._getSymbolsForTimeframe(timeframe))

        symbol_timeframe_pairs = [(timeframe, symbol) for timeframe in self.exchange.getTimeFrames() for symbol in self._getSymbolsForTimeframe(timeframe) ]

        while True:
            try:
                # Process symbols in groups
                group_size = self.process_group_number
                for i in range(0, len(symbol_timeframe_pairs), group_size):
                    symbol_group = symbol_timeframe_pairs[i:i+group_size]
                    # this because the blacklist is dynamic
                    symbol_group = [(timeframe, symbol) for timeframe, symbol in symbol_group if symbol not in self.exchange.getBlackList()]
                    # symbol_group = [(timeframe, symbol) for timeframe, symbol in symbol_group if symbol not in self.exchange.getBlackList()]
                    tasks = [self._process_symbol(symbol, self._traders_pool_factory(f"{symbol} {timeframe}"), timeframe=timeframe) for timeframe, symbol  in symbol_group]
                    await asyncio.gather(*tasks)

                await asyncio.sleep(self.exchange.sleep_time)
            except Exception as e:
                print(f"Error occurred: {e}")
                
        print("done")

    async def _fetch_data(self,symbol, attempts=1, sleep_time=1, timeframe='1d'):
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
        # async with self.fetch_semaphore:
        max_candles_to_fetch = self.exchange.getMaxCandlesToFetch()
        for i in range(attempts):
            try:
                df = self.exchange.get_ohlcv_Data(symbol, timeframe, max_candles_to_fetch=max_candles_to_fetch)
                if df.empty:
                    raise ValueError(f"No data returned for {symbol}")
                if len(df) < max_candles_to_fetch:
                    raise ValueError(f"Insufficient data returned for {symbol}")
                return df
            except Exception as e:
                print(f"Attempt {i+1} failed for {symbol}: {e}")
                await asyncio.sleep(sleep_time)
        # raise Exception(f"Failed to fetch data for {symbol} after {attempts} attempts")

    async def _print_trader_state(self,title, state, last_close, console):
        now = datetime.datetime.now(datetime.UTC)
        # last_close = df['close'].iloc[-1]
        color = "yellow"
        if 'buy' in state:
            color = 'green'
        elif 'sell' in state:
            color = 'red'
            # Do something with last_close
        console.print(f"[bold]{now}[/bold] | {title} | [bold {color}]{state}[/bold {color}] | [bold]{last_close}[/bold]")
        print()

    async def _process_symbol(self, symbol:str, trader_info:dict, timeframe='1d')->None:
        async with self.process_semaphore:
            # Data fetch
            df:pd.DataFrame = await self._fetch_data(symbol, timeframe=timeframe)
            
            # Data validation
            if df is None:
                self.exchange.appendToBlackList(symbol)
                print(f"Blacklisted {symbol}")
                return
            
            # last_row = df.iloc[-1]
            if df.iloc[-1].isnull().any():
                print(f"skip {symbol}")
                return

            trader:TradingStateMachine = trader_info['trader']
            trader_info["datetime"] = datetime.datetime.now(datetime.UTC)
            
            # todo: we know the model, so we can optimise the enrichment
            # i read 1000 rows but i calculate only data for the last row
            # trader.enrich_dataset(df)
            # sample_df:pd.DataFrame = self.getDataFrame(df)
           
            old_state = trader.state     
            sample_df:pd.DataFrame = self.getDataFrame(df).reset_index().copy()
            trader.enrich_dataset(sample_df)
            trader.process(sample_df)
            
            if BUILD_DATASET_COLLECTION:
                sample_df.to_csv(f"./Data/bybit/{symbol.replace('/','-')}_{timeframe}.csv")
                print(f"Saved {symbol} {timeframe} data")
                return
             
            if old_state != trader.state:   
                await self._print_trader_state(trader.strategy.getSymbolAndTimeFrame(), trader.state, sample_df['close'].iloc[-1], console)




if __name__ == "__main__":
    
    async def run_bot():
        exchange:ExchangeManagement = BackTesting()
        
        print(f"Starting bot for {exchange.getExchangeName()}")
        trading_system = TradingSystem(exchange)
        return await trading_system.run()
    
    console.print()
    console.print()
    console.print(" #####                              ")
    console.print("#     #  ####    ##   #      #####  ")
    console.print("#       #    #  #  #  #      #    # ")
    console.print(" #####  #      #    # #      #    # ")
    console.print("      # #      ###### #      #####  ")
    console.print("#     # #    # #    # #      #      ")
    console.print(" #####   ####  #    # ###### #      ")
    console.print()
    console.print()
    asyncio.run(run_bot())
    