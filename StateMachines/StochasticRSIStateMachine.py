from pandas import DataFrame
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine
from ta.momentum import StochRSIIndicator
import common

class StochasticRSIStateMachine(AbstractDataStateMachine):

    def __init__(self):
        super().__init__()  # Call the constructor of the superclass
        # Additional initialization code for the subclass

    def configure_states(self):
        self.states = ['neutral', 'bullish_crossover', 'bearish_crossover']
        # self.initial_state = 'neutral'
        self.configure_machine()

    def _identify_bullish_crossover(self,df:DataFrame):
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
        


    def _identify_bearish_crossover(self,df:DataFrame):
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

    def _identify_oversold(self, df:DataFrame, lower_threshold=0.2):

        return (df['stoch_rsi_k'] < lower_threshold) | ((df['stoch_rsi_d'] < lower_threshold) | ((df['stoch_rsi_k'] == 0) & (df['stoch_rsi_d'] == 0)))
    
    def _identify_overbought(self, df:DataFrame, upper_threshold=0.8):

        return (df['stoch_rsi_k'] > upper_threshold) | (df['stoch_rsi_d'] > upper_threshold)
    
    def _determine_trend(self, df:DataFrame):
        """
        Determines the trend based on the most recent bullish or bearish crossover.

        Parameters:
        - df: DataFrame with 'bullish_crossover' and 'bearish_crossover' columns.

        Returns:
        - String indicating the trend: 'Bullish', 'Bearish', or 'Neutral'.
        """
        
                
        last_bullish_crossover_index = df[df['stoch_rsi_bullish_crossover']].index.max()
        last_bearish_crossover_index = df[df['stoch_rsi_bearish_crossover']].index.max()

                    
        # If both crossovers are present, check which one is most recent
        # if df['stoch_rsi_bullish_crossover'].any() and df['stoch_rsi_bearish_crossover'].any():
        if last_bullish_crossover_index and last_bearish_crossover_index:

            if last_bullish_crossover_index > last_bearish_crossover_index:
                return 'BullishCrossover'
            elif last_bearish_crossover_index > last_bullish_crossover_index:
                return 'BearishCrossover'
        
        elif last_bullish_crossover_index:
            return 'BullishCrossover'
        elif last_bearish_crossover_index:
            return 'BearishCrossover'
        
        # Default case if none of the above conditions are met
        return 'Neutral'


    def enrich_dataset(self, df:DataFrame):
        df['stoch_rsi'] = StochRSIIndicator(df['close']).stochrsi()
        df['stoch_rsi_k'] = StochRSIIndicator(df['close']).stochrsi_k()
        df['stoch_rsi_d'] = StochRSIIndicator(df['close']).stochrsi_d()
        df['stoch_rsi_overbought'] = self._identify_overbought(df)
        df['stoch_rsi_oversold'] = self._identify_oversold(df)
        df['stoch_rsi_bullish_crossover'] = self._identify_bullish_crossover(df)
        df['stoch_rsi_bearish_crossover'] = self._identify_bearish_crossover(df)
        
        df['stoch_rsi_slope'] = common.calc_slope(df,'stoch_rsi')
        df['stoch_rsi_k_slope'] = common.calc_slope(df,'stoch_rsi_k')
        df['stoch_rsi_d_slope'] = common.calc_slope(df,'stoch_rsi_d')
        df['stoch_rsi_trend'] = common.calc_trend(df,'stoch_rsi_slope')
        df['stoch_rsi_change_of_trend'] = common.calc_change_of_trend(df,'stoch_rsi_trend')
        self.trend = common.last_value(df,'stoch_rsi_trend')
        self.change_of_trend = common.last_value(df,'stoch_rsi_change_of_trend')
        pass

    def print_df(self, df:DataFrame):
        print(df[['timestamp', 'close', 'stoch_rsi', 'stoch_rsi_k', 'stoch_rsi_d', 'stoch_rsi_overbought', 'stoch_rsi_oversold', 'stoch_rsi_bullish_crossover', 'stoch_rsi_bearish_crossover']])

    def configure_transitions(self):
        self.machine.add_transition('to_bullish_crossover', '*', 'bullish_crossover', conditions=['is_bullish_crossover'])
        self.machine.add_transition('to_bearish_crossover', '*', 'bearish_crossover', conditions=['is_bearish_crossover'])
        self.machine.add_transition('to_neutral', '*', 'neutral', conditions=['is_neutral'])

        
    def process(self, df:DataFrame):

        try:
            trend = self._determine_trend(df)
            if self.is_bullish_crossover(trend):
                if self.state != 'bullish_crossover':
                    self.to_bullish_crossover()
                
            elif self.is_bearish_crossover(trend):
                if self.state != 'bearish_crossover':
                    self.to_bearish_crossover()
                    
            elif self.is_neutral(trend):
                if self.state != 'neutral':
                    self.to_neutral()

        except Exception as e:
            print(f"An exception occurred: {e}")

    def is_bullish_crossover(self, trend):
        return trend == 'BullishCrossover'

    def is_bearish_crossover(self, trend):
        return trend == 'BearishCrossover'

    def is_neutral(self, trend):
        # This might need additional logic to determine 'flat' slope accurately
        return trend == 'Neutral'

    def is_data_oversold(self, df:DataFrame):
        return df['stoch_rsi_oversold'].iloc[-1] 
        # return False

    def is_data_overbought(self, df:DataFrame):
        return df['stoch_rsi_overbought'].iloc[-1] 
        # return False