import asyncio
from pandas import DataFrame
import pandas as pd
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from ta.momentum import StochRSIIndicator
from ta.trend import MACD
import common

class SimpleTradingStrategy(AbstractTradingStrategy):
    
    __slots__ = ['buy_price', 'sell_price', 'signal', 'period', 'hma_column', 'model_df']
    
    def __init__(self, symbol:str):
        self.period = 200
        self.hma_column = f'hma{self.period}'
        self.model_df = self.read_model()
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
        df['stoch_rsi_change_of_trend_'] = common.calc_change_of_trend(df,'stoch_rsi_trend_')
        
        df[self.hma_column] = common.hull_moving_average(df['close'],self.period)
        df[f'{self.hma_column}_slope'] = common.calc_slope(df,self.hma_column)
        df[f'{self.hma_column}_trend_'] = common.calc_trend(df,f'{self.hma_column}_slope')
        df[f'{self.hma_column}_change_of_trend_'] = common.calc_change_of_trend(df,f'{self.hma_column}_trend_')
        df[f'{self.hma_column}_above_price_'] = df[self.hma_column] > df['close']
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
        df['macd_slope'] = common.calc_slope(df,'macd')
        df['macd_signal_slope'] = common.calc_slope(df,'macd_signal')
        df['macd_trend_'] = common.calc_trend(df,'macd_slope')
        df['macd_change_of_trend_'] = common.calc_change_of_trend(df,'macd_trend_')

    def last_value_of(self,df:DataFrame,column:str):
        return df[column].iloc[-1]

    def last_row_of(self,df:DataFrame):
        return df.iloc[-1].to_dict()

    async def print_data(self, df_row:dict, last_close:float):
        await self.print_no_repeat_async("value", f"{last_close}")
        tasks = []
        for key in df_row:
            if key[-1] == "_":
                tasks.append(asyncio.create_task(self.print_no_repeat_async(key, f"{key}: {df_row[key]}")))
        await asyncio.gather(*tasks)


    def process(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        
        # this must be done very fast
        self.signal = self.apply_model_and_check_signal(df)
        self.last_close = df['close'].iloc[-1]          
        # print data
        asyncio.create_task(self.print_data(self.last_row_of(df), self.last_close))
        
    
    def onBuy(self):
        self.buy_price = self.last_close
        pass
    def onSell(self):
        self.sell_price = self.last_close
        pass
    def onStopBuy(self):
        self.buy_price = None
        pass
    def onStopSell(self):
        self.sell_price = None
        pass
    
    def read_model(self) -> DataFrame:
        # the model is a dataframe containing the feature columns and their value plus a column called "action" which is the target
        
        model_buy:DataFrame = pd.read_csv("./simple_model_buy.csv")
        model_sell:DataFrame = pd.read_csv("./simple_model_sell.csv")

        model:DataFrame = pd.concat([model_buy, model_sell], ignore_index=True)
        return model
    
    def apply_model_and_check_signal(self, df:DataFrame):
        # apply the model to the dataframe
        # match the columns in the model with the columns in the dataframe
        try:
            df_columns = set(df.columns)
            model_columns = set(self.get_features_list(self.model_df))
            intersect_columns = list(df_columns.intersection(model_columns))

            # min_diff = 999
            if len(intersect_columns) == len(model_columns):
                current_df_slice = df.loc[df.index[-1], intersect_columns]
                for df_model_index in range(len(self.model_df)):
                    current_model_slice = self.model_df.loc[df_model_index, intersect_columns]
                    if current_df_slice.equals(current_model_slice):
                        return self.model_df.loc[df_model_index, 'signal']
                
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return "Error"
            # Handle the error or raise it again if needed
        pass
    
    def should_buy(self):
        """Buy if both MACD and Stochastic indicators are in their bullish states."""
        return self.signal == "Buy"
        pass
    
    def should_stopbuy(self):
        """Determines whether to stop buying based on indicator states."""
        # add stop loss and take profit
        return self.buy_price is not None and self.last_close > self.buy_price * 1.05
        pass
    
    def should_sell(self):
        """Sell if both MACD and Stochastic indicators are in their bearish states."""
        return self.signal == "Sell"
        pass

    def should_stopsell(self):
        """Determines whether to stop selling based on indicator states."""
        # add stop loss and take profit
        return self.sell_price is not None and self.last_close < self.sell_price * 0.95
        pass