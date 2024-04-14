import asyncio
from pandas import DataFrame, Series
import pandas as pd
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
import Markov

class FeatureExtractionStrategy(AbstractTradingStrategy):

    def __init__(self, symbol:str):
        self.hma_period = 200
        self.hma_column:str = f'hma{self.hma_period}'
        super().__init__(symbol=symbol)

    def enrich_dataset(self, df:DataFrame):
        self.required_columns:list = self._compute_required_columns(self.feature_calculations.keys())
        print("required columns: ", self.required_columns)
        
        items = self.feature_calculations.items()
        print("columns do generate: ", len(items))
        for feature, function in items:
            if feature in self.required_columns:
                print("generating feature: ", feature)
                function(df)
        print(list(df.columns))
        pass

    def should_buy(self):
        pass
    
    def should_stopbuy(self):
        pass
    
    def should_sell(self):
        pass

    def should_stopsell(self):
        pass

    def process(self, df:DataFrame, balance:float):
        pass

class SimpleTradingStrategy(AbstractTradingStrategy):

    __slots__ = ['hma_period', 'hma_column', 'model_df', 'required_columns', 'first_time', 'stop_perc', 'macd_last_crossover', 'transition_matrix', 'signal', 'pause']    
    
    def __init__(self, symbol:str):
        self.hma_period = 200
        self.hma_column:str = f'hma{self.hma_period}'
        self.model_df:DataFrame = self._read_model()
        self.required_columns:list = self._compute_required_columns(list(self.model_df.columns))
        self.first_time = True
        self.stop_perc = 0.005
        self.macd_last_crossover = None
        self.transition_matrix = Markov.read_transition_matrix()
        self.signal = None
        self.pause = 0
        super().__init__(symbol=symbol)

    def enrich_dataset(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states.""" 
        for feature, function in self.feature_calculations.items():
            if feature in self.required_columns:
                function(df)
        pass

    async def print_data(self, df_row:dict, balance: float, last_close:float):
        await self.print_no_repeat_async("value", f"{last_close} | {balance}",now= df_row['timestamp'])
        # the list of correct columns can be precalculated the first time the model is read
        tasks = [asyncio.create_task(self.print_no_repeat_async(key, f"{key}: {df_row[key]}", now=df_row['timestamp'])) for key in df_row if key[-1] == "_"]
        await asyncio.gather(*tasks)


    def process(self, df:DataFrame, balance:float):
        """Determines whether to execute a sell based on indicator states."""
        
        if self.pause > 0:
            self.pause -= 1
            return
         
        if self.first_time:
            # df_columns = set(df.columns)
            model_columns = set(self.get_features_list(self.model_df))
            # self.intersect_columns = list(df_columns.intersection(model_columns))
            intersect_columns = set(self.required_columns).intersection(model_columns)
            if len(intersect_columns) != len(model_columns):
                raise ValueError(f"Model columns do not match the columns in the dataframe. Model columns: {model_columns}, Dataframe columns: {self.required_columns}")
            self.intersect_columns = list(intersect_columns)
            self.first_time = False
        
        # this must be done very fast
        
        # pattern = Markov.last_five_candle_pattern(df)
        # pattern_prediction = Markov.predict_N_steps_ahead(pattern, self.transition_matrix, steps=3)
        # print("Pattern: ", pattern, "Prediction: ", pattern_prediction)
        
        df_last = super().last_row_of(df) 
        self.last_close = df_last['close']  
        self.max_price = max(self.max_price, self.last_close)
        self.min_price = min(self.min_price, self.last_close)  

        signal = self.generate_buy_sell_signals(df_last)

        if signal == 1:
            # if pattern_prediction.endswith('G'):
                self.signal = signal
        elif signal == -1:
            # if pattern_prediction.endswith('R'):
                self.signal = signal

        # print data
        asyncio.create_task(self.print_data(self.last_row_of(df), balance, self.last_close))
        
    def onBuy(self):
        self.buy_price = self.last_close
        self.max_price = self.last_close
        self.min_price = self.last_close
        pass
    def onSell(self):
        self.sell_price = self.last_close
        self.max_price = self.last_close
        self.min_price = self.last_close
        pass
    def onStopBuy(self):
        # self.buy_price = None
        self.pause = 5
        pass
    def onStopSell(self):
        # self.sell_price = None
        self.pause = 5
        pass
    
    def _read_model(self) -> DataFrame:
        
        model:DataFrame = pd.read_csv("./simple_model.csv")
        
        df_columns = set(model.columns)
        columns_to_remove = [col for col in df_columns if col != 'signal' and not col.endswith('_')]
        model = model.drop(columns=columns_to_remove)
        return model
    
    def generate_buy_sell_signals(self, df_last:dict):

        try:

            if False:
                current_df_slice = df.loc[df.index[-1], self.intersect_columns]
                for df_model_index in range(len(self.model_df)):
                    current_model_slice = self.model_df.loc[df_model_index, self.intersect_columns]
                    if current_df_slice.equals(current_model_slice):
                        return self.model_df.loc[df_model_index, 'signal']
            
            if self.macd_last_crossover is None:    
                if df_last['macd_bullish_crossover_']==True:
                    self.macd_last_crossover = 1
                if df_last['macd_bearish_crossover_']==True:
                    self.macd_last_crossover = -1    
            
            if self.signal != 1:    
                if (self.macd_last_crossover==1 
                    and df_last['macd_trend_']==1 
                    and df_last['stoch_rsi_oversold_']==True 
                    and df_last['hma200_trend_']==True
                    and df_last['hma200_above_price_']==False):
                    self.macd_last_crossover = None
                    return 1       
            
            if self.signal != -1:
                if (self.macd_last_crossover==-1 
                    and df_last['macd_trend_']==-1 
                    and df_last['stoch_rsi_overbought_']==True
                    and df_last['hma200_trend_']==False
                    and df_last['hma200_above_price_']==True):
                    self.macd_last_crossover = None
                    return -1 
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return "Error"
            # Handle the error or raise it again if needed
        pass
    
    def should_buy(self):
        return self.signal == 1
        pass
    
    def should_stopbuy(self):
        """Determines whether to stop buying based on indicator states."""
        # add stop loss and take profit
        if self.buy_price is None:
            return False
        
        if self.last_close < self.buy_price:
            return True
        
        # stop buy
        if self.last_close < self.max_price * (1 - self.stop_perc):
            return True
        
        return False
    
    def should_sell(self):
        return self.signal == -1
        pass

    def should_stopsell(self):
        """Determines whether to stop selling based on indicator states."""
        # add stop loss and take profit
        
        if self.sell_price is None:
            return False

        if self.last_close > self.sell_price:
            return True
        
        # trailing stop sell
        if self.last_close > self.min_price * (1 + self.stop_perc):
            return True
        
        return False
