from pandas import DataFrame
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine
# from ta.momentum import StochRSIIndicator
from ta.trend import EMAIndicator
import common 

class HullMovingAverageStateMachine(AbstractDataStateMachine):

    def __init__(self, period=200):
        super().__init__()  # Call the constructor of the superclass
        # Additional initialization code for the subclass
        self.period = period
        self.column = f'hma{self.period}'
    
    def configure_states(self):
        self.states = ['neutral', 'uptrend', 'downtrend']
        # self.initial_state = 'neutral'
        self.configure_machine()
        
    def enrich_dataset(self, df:DataFrame):
        df[self.column] = EMAIndicator(df['close'],self.period).ema_indicator()
        df[f'{self.column}_slope'] = common.calc_slope(df,self.column)
        df[f'{self.column}_trend'] = common.calc_trend(df,f'{self.column}_slope')
        df[f'{self.column}_change_of_trend'] = common.calc_change_of_trend(df,f'{self.column}_trend')
        self.change_of_trend = common.last_value(df,f'{self.column}_change_of_trend')
        self.trend = common.last_value(df,f'{self.column}_trend')
        df[f'{self.column}_above_price'] = df[self.column] > df['close']
        self.above_price = common.last_value(df,f'{self.column}_above_price')
        pass

    def print_df(self, df:DataFrame):
        print(df[['timestamp', 'close', self.column]])

    def configure_transitions(self):
        self.machine.add_transition('to_uptrend', '*', 'uptrend', conditions=['is_uptrend'])
        self.machine.add_transition('to_downtrend', '*', 'downtrend', conditions=['is_downtrend'])
        self.machine.add_transition('to_neutral', '*', 'neutral', conditions=['is_neutral'])

    def process(self, df:DataFrame):
        pass
    
        # try:
            
        #     # if self.is_price_above(df):
        #     #     if self.state != 'uptrend':
        #     #         self.to_uptrend()

        #     # if self.is_price_below(df):
        #     #     if self.state != 'downtrend':
        #     #         self.to_downtrend()

        # except Exception as e:
        #     print(f"An exception occurred: {e}")

    def is_uptrend(self, df:DataFrame):
        return self.trend == 'Uptrend'
    
    def is_downtrend(self, df:DataFrame):
        return self.trend == 'Downtrend'

    # def is_price_above(self, df:DataFrame):
    #     return df[self.column].iloc[-1] < df['close'].iloc[-1] 

    # def is_price_below(self, df:DataFrame):
    #     return df[self.column].iloc[-1] > df['close'].iloc[-1]

    def is_neutral(self, trend):
        # This might need additional logic to determine 'flat' slope accurately
        return False
