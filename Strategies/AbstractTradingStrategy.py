from abc import ABC, abstractmethod
import datetime

from pandas import DataFrame, Series
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine

class AbstractTradingStrategy(ABC):
    
    def __init__(self, symbol=''):
        self.last_printed_value = None
        self.symbol = symbol
    
    def print_no_repeat(self, value):
        if value != self.last_printed_value:
            now = datetime.datetime.now(datetime.UTC)
            print(f"{now} | {self.symbol} | {value}")
            # print(value)
            self.last_printed_value = value    
    
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

    # def apply_strategy(self, trader:AbstractDataStateMachine):
    #     """Applies the strategy sending messages to the state machine."""
    #     pass