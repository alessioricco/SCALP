from abc import ABC, abstractmethod
import datetime
from pandas import DataFrame, Series
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine
from rich.console import Console
console = Console()

class AbstractTradingStrategy(ABC):
    
    def __init__(self, symbol=''):
        self.last_printed_value = {}
        self.symbol = symbol
    
    def print_no_repeat(self, key, value):
        if key not in self.last_printed_value:
            self.last_printed_value[key] = None
        if value != self.last_printed_value[key]:
            now = datetime.datetime.now(datetime.UTC)
            console.print(f"{now} | {self.symbol} | {value}")
            # print(value)
            self.last_printed_value[key] = value    
    
    def getSymbolAndTimeFrame(self):
        return self.symbol
    
    @staticmethod
    def get_features_list(df:DataFrame):
        return [x for x in df.columns if x[-1] == "_"]
    
    @abstractmethod
    def enrich_dataset(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        pass    
    
    @abstractmethod
    def should_buy(self):
        """Determines whether to execute a buy based on indicator states."""
        pass

    @abstractmethod
    def should_sell(self):
        """Determines whether to execute a sell based on indicator states."""
        pass

    @abstractmethod
    def should_stopbuy(self):
        """Determines whether to stop buying based on indicator states."""
        pass

    @abstractmethod
    def should_stopsell(self):
        """Determines whether to stop selling based on indicator states."""
        pass

    @abstractmethod
    def process(self, index, row:Series, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        pass

