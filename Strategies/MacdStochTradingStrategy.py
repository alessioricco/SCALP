from pandas import DataFrame, Series
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine
from StateMachines.MACDStateMachine import MACDStateMachine
from StateMachines.StochasticRSIStateMachine import StochasticRSIStateMachine
from StateMachines.TradingStateMachine import TradingStateMachine


class MacdStochRSITradingStrategy(AbstractTradingStrategy):
    
    __slots__ = ['macd_sm', 'stochastic_sm', 'macd_state', 'stochastic_state']
    
    def __init__(self, symbol:str, macd_state_machine:MACDStateMachine, stochastic_state_machine:StochasticRSIStateMachine):
        self.macd_sm:MACDStateMachine = macd_state_machine
        self.stochastic_sm:StochasticRSIStateMachine = stochastic_state_machine
        super().__init__(symbol=symbol)
        # self.last_printed_value = None

    def enrich_dataset(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        self.macd_sm.enrich_dataset(df)   
        self.stochastic_sm.enrich_dataset(df)

    def process(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        self.macd_sm.process(df)
        self.stochastic_sm.process(df)
        self.macd_state = self.macd_sm.getCurrentState()
        self.stochastic_state = self.stochastic_sm.getCurrentState()
        self.print_no_repeat(f"MACD: {self.macd_state} STOCHRSI: {self.stochastic_state}")
        pass
        
    def should_buy(self):
        """Buy if both MACD and Stochastic indicators are in their bullish states."""
        # macd_state = self.macd_sm.getCurrentState()
        # stochastic_state = self.stochastic_sm.getCurrentState()
        return self.macd_state == 'bullish_cross' and self.stochastic_state == 'bullish'
    
    def should_sell(self):
        """Sell if both MACD and Stochastic indicators are in their bearish states."""
        # macd_state = self.macd_sm.getCurrentState()
        # stochastic_state = self.stochastic_sm.getCurrentState()
        return self.macd_state == 'bearish_cross' and self.stochastic_state == 'bearish'
    
    def should_stopbuy(self):
        """Determines whether to stop buying based on indicator states."""
        # macd_state = self.macd_sm.getCurrentState()
        # stochastic_state = self.stochastic_sm.getCurrentState()
        return self.macd_state == 'bearish_cross' or self.stochastic_state == 'bearish'
    
    def should_stopsell(self):
        """Determines whether to stop selling based on indicator states."""
        # macd_state = self.macd_sm.getCurrentState()
        # stochastic_state = self.stochastic_sm.getCurrentState()
        return self.macd_state == 'bullish_cross' or self.stochastic_state == 'bullish'

