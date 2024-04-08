from pandas import DataFrame
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from ta.momentum import StochRSIIndicator
from ta.trend import MACD
import common

class SimpleTradingStrategy(AbstractTradingStrategy):
    
    # __slots__ = ['stochastic_sm', 'stochastic_state', 'stochastich_overbought', 'stochastich_oversold']
    
    def __init__(self, symbol:str):
        # self.stochastic_sm:StochasticRSIStateMachine = stochastic_state_machine
        # self.hma_sm:HullMovingAverageStateMachine = hma_state_machine
        # self.macd_sm:MACDStateMachine = macd_state_machine
        self.period = 200
        self.column = f'hma{self.period}'
        super().__init__(symbol=symbol)

    def calc_stoch_rsi_bullish_crossover(self,df:DataFrame):
        """
        Identifies bullish crossovers when stoch_rsi_k crosses above stoch_rsi_d.
        Returns a Series where True indicates a bullish crossover.
        """
        # Shift stoch_rsi_k by one to compare previous values with current stoch_rsi_d
        prev_stoch_rsi_k = df['stoch_rsi_k'].shift(1)
        prev_stoch_rsi_d = df['stoch_rsi_d'].shift(1)

        # Bullish crossover condition
        bottom = ((prev_stoch_rsi_k == 0) & (prev_stoch_rsi_d == 0)) & ((df['stoch_rsi_k'] > 0) | (df['stoch_rsi_d'] > 0))

        return bottom | ((prev_stoch_rsi_k < prev_stoch_rsi_d) & (df['stoch_rsi_k'] > df['stoch_rsi_d']))
        


    def calc_stoch_rsi_bearish_crossover(self,df:DataFrame):
        """
        Identifies bearish crossovers when stoch_rsi_k crosses below stoch_rsi_d.
        Returns a Series where True indicates a bearish crossover.
        """
        # Shift stoch_rsi_k by one to compare previous values with current stoch_rsi_d
        prev_stoch_rsi_k = df['stoch_rsi_k'].shift(1)
        prev_stoch_rsi_d = df['stoch_rsi_d'].shift(1)

        # Bearish crossover condition
        top =  ((prev_stoch_rsi_k == 1) & (prev_stoch_rsi_d == 1)) & ((df['stoch_rsi_k'] < 1) | (df['stoch_rsi_d'] < 1))
        return top | ((prev_stoch_rsi_k > prev_stoch_rsi_d) & (df['stoch_rsi_k'] < df['stoch_rsi_d'])) 

    def calc_stoch_rsi_oversold(self, df:DataFrame, lower_threshold=0.2):

        return (df['stoch_rsi_k'] < lower_threshold) | ((df['stoch_rsi_d'] < lower_threshold) | ((df['stoch_rsi_k'] == 0) & (df['stoch_rsi_d'] == 0)))
    
    def calc_stoch_rsi_overbought(self, df:DataFrame, upper_threshold=0.8):

        return (df['stoch_rsi_k'] > upper_threshold) | (df['stoch_rsi_d'] > upper_threshold)

    def enrich_dataset(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states.""" 
        df['stoch_rsi'] = StochRSIIndicator(df['close']).stochrsi()
        df['stoch_rsi_k'] = StochRSIIndicator(df['close']).stochrsi_k()
        df['stoch_rsi_d'] = StochRSIIndicator(df['close']).stochrsi_d()
        df['stoch_rsi_overbought_'] = self.calc_stoch_rsi_overbought(df)
        df['stoch_rsi_oversold_'] = self.calc_stoch_rsi_oversold(df)
        df['stoch_rsi_bullish_crossover_'] = self.calc_stoch_rsi_bullish_crossover(df)
        df['stoch_rsi_bearish_crossover_'] = self.calc_stoch_rsi_bearish_crossover(df)
        df['stoch_rsi_slope'] = common.calc_slope(df,'stoch_rsi')
        df['stoch_rsi_k_slope'] = common.calc_slope(df,'stoch_rsi_k')
        df['stoch_rsi_d_slope'] = common.calc_slope(df,'stoch_rsi_d')
        df['stoch_rsi_trend_'] = common.calc_trend(df,'stoch_rsi_slope')
        df['stoch_rsi_change_of_trend_'] = common.calc_change_of_trend(df,'stoch_rsi_trend')
        
        df[self.column] = common.hull_moving_average(df['close'],self.period)
        df[f'{self.column}_slope'] = common.calc_slope(df,self.column)
        df[f'{self.column}_trend'] = common.calc_trend(df,f'{self.column}_slope')
        df[f'{self.column}_change_of_trend_'] = common.calc_change_of_trend(df,f'{self.column}_trend')
        df[f'{self.column}_above_price_'] = df[self.column] > df['close']
        # self.above_price = common.last_value(df,f'{self.column}_above_price')
        
        # Assuming MACD and Signal Line have already been calculated
        df['macd'] = MACD(df['close']).macd()
        df['macd_signal'] = MACD(df['close']).macd_signal()
        # Calculate the difference between MACD and its Signal Line
        df['macd_diff']=MACD(df['close']).macd_diff()
        df['prev_macd_diff'] = df['macd_diff'].shift(1)
        # Identify bullish crossover with both MACD and signal lines being negative
        df['macd_bullish_crossover_'] = ((df['macd_diff'] > 0) & (df['prev_macd_diff'] <= 0)) 
        # Identify bearish crossover with both MACD and signal lines being positive
        df['macd_bearish_crossover_'] = ((df['macd_diff'] < 0) & (df['prev_macd_diff'] >= 0)) 
        df['macd_positive_'] = df['macd_diff'] >= 0
        # df['macd_bullish_crossover_positive_'] = df['macd_bullish_crossover_'] & df['macd_negative']
        # df['macd_bearish_crossover_negative_'] = df['macd_bearish_crossover_'] & df['macd_positive_']       
        df['macd_slope'] = common.calc_slope(df,'macd')
        df['macd_signal_slope'] = common.calc_slope(df,'signal')
        df['macd_trend_'] = common.calc_trend(df,'macd_slope')
        df['macd_change_of_trend_'] = common.calc_change_of_trend(df,'macd_trend')

    def last_value_of(self,df:DataFrame,column:str):
        return df[column].iloc[-1]

    def last_row_of(self,df:DataFrame):
        return df.iloc[-1].to_dict()

    def process(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        # self.stochastic_sm.process(df)
        # self.stochastic_state = self.stochastic_sm.getCurrentState()
        
        df_row = self.last_row_of(df)
        
        for key in df_row:
            # print(f"{key} : {df_row[key]}")
            if key[-1] == "_":
                self.print_no_repeat(key,f"{key}: {df_row[key]}")
        
        # stochastich_overbought = df_row["stoch_rsi_overbought_"] #self.stochastic_sm.is_data_overbought(df)
        # stochastich_oversold = df_row["stoch_rsi_oversold_"] #self.stochastic_sm.is_data_oversold(df)
        
        # # self.print_no_repeat("stochrsi_state",f"STOCHRSI: [bold]{self.stochastic_state}[/bold]")
        # if stochastich_overbought:
        #     self.print_no_repeat("stochrsi_over","STOCHRSI: Overbought")
        # if stochastich_oversold:
        #     self.print_no_repeat("stochrsi_over","STOCHRSI: Oversold")
        # self.print_no_repeat("stochrsi__trend",f"STOCHRSI trend : [bold]{df_row['stoch_rsi_trend']}[/bold]")
        # self.print_no_repeat("stochrsi__cot  ",f"STOCHRSI c_o_t : [bold]{df_row['stoch_rsi_change_of_trend']}[/bold]")

        # # self.hma_sm.process(df)
        # # self.hma_sm_state = self.hma_sm.getCurrentState()
        
        # # self.print_no_repeat("hma_state",f"HMA       : [bold]{self.hma_sm_state}[/bold]")
        # self.print_no_repeat("hma_trend",f"HMA trend : [bold]{df_row[f'{self.column}_trend']}[/bold]")
        # self.print_no_repeat("hma_cot  ",f"HMA c_o_t : [bold]{f'{self.column}_change_of_trend'}[/bold]")
        # self.print_no_repeat("hma>Close",f"HMA > $   : [bold]{f'{self.column}_above_price'}[/bold]")
        
        # # self.macd_sm.process(df)
        # # self.macd_sm_state = self.macd_sm.getCurrentState()
        # # self.print_no_repeat("macd",        f"MACD      : [bold]{self.macd_sm_state}[/bold]")
        # self.print_no_repeat("macd_trend",  f"MACD trend: [bold]{df_row['macd_trend']}[/bold]")
        # self.print_no_repeat("macd_cot  ",  f"MACD c_o_t: [bold]{df_row['macd_change_of_trend']}[/bold]")
        
        # # if self.macd_sm.macd_positive:
        # self.print_no_repeat("macd_zero",f"MACD > 0   : {df_row['macd_positive']}")
        # # else:
        # # # elif self.macd_sm.macd_negative:
        # #     self.print_no_repeat("macd_zero","MACD      : Negative")
        
        pass
        
    def should_buy(self):
        """Buy if both MACD and Stochastic indicators are in their bullish states."""
        # return (
        #         # self.hma_sm_state == 'uptrend' and
        #         self.macd_sm.macd_negative and 
        #         self.macd_sm_state=="bullish_cross" and
        #         (self.stochastich_oversold or self.stochastic_state == 'bullish_crossover') and
        #         not self.stochastich_overbought
        #         )
        pass
    
    def should_stopbuy(self):
        """Determines whether to stop buying based on indicator states."""
        # if self.hma_sm_state == 'downtrend':
        #     return True
        # return (self.hma_sm_state == 'downtrend' or
        #         self.macd_sm.macd_positive or 
        #         self.stochastich_overbought or  
        #         self.stochastic_state == 'bearish_crossover')
        pass
    
    def should_sell(self):
        """Sell if both MACD and Stochastic indicators are in their bearish states."""
        # if not self.hma_sm_state == 'downtrend':
        #     return False
        # return self.macd_sm.macd_positive and self.stochastich_overbought and self.stochastic_state == 'bearish_crossover'
        # return (
        #         # self.hma_sm_state == 'downtrend' and
        #         self.macd_sm.macd_positive and 
        #         self.macd_sm_state=="bearish_cross" and
        #         (self.stochastich_overbought or self.stochastic_state == 'bearish_crossover') and 
        #         not self.stochastich_oversold)
        pass

    def should_stopsell(self):
        """Determines whether to stop selling based on indicator states."""
        # if self.hma_sm_state == 'uptrend':
        #     return True
        # return (self.hma_sm_state == 'uptrend' or 
        #         self.macd_sm.macd_negative or 
        #         self.stochastich_oversold or 
        #         self.stochastic_state == 'bullish_crossover')
        pass