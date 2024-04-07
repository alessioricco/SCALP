from pandas import DataFrame
from StateMachines.HullMovingAverageStateMachine import HullMovingAverageStateMachine
from StateMachines.MACDStateMachine import MACDStateMachine
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from StateMachines.StochasticRSIStateMachine import StochasticRSIStateMachine


class StochRSITradingStrategy(AbstractTradingStrategy):
    
    # __slots__ = ['stochastic_sm', 'stochastic_state', 'stochastich_overbought', 'stochastich_oversold']
    
    def __init__(self, symbol:str, stochastic_state_machine:StochasticRSIStateMachine, hma_state_machine:HullMovingAverageStateMachine, macd_state_machine:MACDStateMachine):
        self.stochastic_sm:StochasticRSIStateMachine = stochastic_state_machine
        self.hma_sm:HullMovingAverageStateMachine = hma_state_machine
        self.macd_sm:MACDStateMachine = macd_state_machine
        super().__init__(symbol=symbol)

    def enrich_dataset(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states.""" 
        self.stochastic_sm.enrich_dataset(df)
        self.hma_sm.enrich_dataset(df)
        self.macd_sm.enrich_dataset(df)

    def process(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        self.stochastic_sm.process(df)
        self.stochastic_state = self.stochastic_sm.getCurrentState()
        self.stochastich_overbought = self.stochastic_sm.is_data_overbought(df)
        self.stochastich_oversold = self.stochastic_sm.is_data_oversold(df)
        
        self.print_no_repeat("stochrsi_state",f"STOCHRSI: [bold]{self.stochastic_state}[/bold]")
        if self.stochastich_overbought:
            self.print_no_repeat("stochrsi_over","STOCHRSI: Overbought")
        if self.stochastich_oversold:
            self.print_no_repeat("stochrsi_over","STOCHRSI: Oversold")
        self.print_no_repeat("stochrsi__trend",f"STOCHRSI trend : [bold]{self.stochastic_sm.trend}[/bold]")
        self.print_no_repeat("stochrsi__cot  ",f"STOCHRSI c_o_t : [bold]{self.stochastic_sm.change_of_trend}[/bold]")

        
        self.hma_sm.process(df)
        self.hma_sm_state = self.hma_sm.getCurrentState()
        
        self.print_no_repeat("hma_state",f"HMA       : [bold]{self.hma_sm_state}[/bold]")
        self.print_no_repeat("hma_trend",f"HMA trend : [bold]{self.hma_sm.trend}[/bold]")
        self.print_no_repeat("hma_cot  ",f"HMA c_o_t : [bold]{self.hma_sm.change_of_trend}[/bold]")
        
        self.macd_sm.process(df)
        self.macd_sm_state = self.macd_sm.getCurrentState()
        self.print_no_repeat("macd",        f"MACD      : [bold]{self.macd_sm_state}[/bold]")
        self.print_no_repeat("macd_trend",  f"MACD trend: [bold]{self.macd_sm.trend}[/bold]")
        self.print_no_repeat("macd_cot  ",  f"MACD c_o_t: [bold]{self.macd_sm.change_of_trend}[/bold]")
        
        if self.macd_sm.macd_positive:
            self.print_no_repeat("macd_zero","MACD      : Positive")
        elif self.macd_sm.macd_negative:
            self.print_no_repeat("macd_zero","MACD      : Negative")
        
        pass
        
    def should_buy(self):
        """Buy if both MACD and Stochastic indicators are in their bullish states."""
        return (
                # self.hma_sm_state == 'uptrend' and
                self.macd_sm.macd_negative and 
                self.macd_sm_state=="bullish_cross" and
                (self.stochastich_oversold or self.stochastic_state == 'bullish_crossover') and
                not self.stochastich_overbought
                )
    
    def should_stopbuy(self):
        """Determines whether to stop buying based on indicator states."""
        # if self.hma_sm_state == 'downtrend':
        #     return True
        return (self.hma_sm_state == 'downtrend' or
                self.macd_sm.macd_positive or 
                self.stochastich_overbought or  
                self.stochastic_state == 'bearish_crossover')
    
    def should_sell(self):
        """Sell if both MACD and Stochastic indicators are in their bearish states."""
        # if not self.hma_sm_state == 'downtrend':
        #     return False
        # return self.macd_sm.macd_positive and self.stochastich_overbought and self.stochastic_state == 'bearish_crossover'
        return (
                # self.hma_sm_state == 'downtrend' and
                self.macd_sm.macd_positive and 
                self.macd_sm_state=="bearish_cross" and
                (self.stochastich_overbought or self.stochastic_state == 'bearish_crossover') and 
                not self.stochastich_oversold)

    def should_stopsell(self):
        """Determines whether to stop selling based on indicator states."""
        if self.hma_sm_state == 'uptrend':
            return True
        return (self.hma_sm_state == 'uptrend' or 
                self.macd_sm.macd_negative or 
                self.stochastich_oversold or 
                self.stochastic_state == 'bullish_crossover')