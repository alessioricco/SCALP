from pandas import DataFrame
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine
from ta.momentum import StochRSIIndicator

class StochasticRSIStateMachine(AbstractDataStateMachine):

    def __init__(self):
        super().__init__()  # Call the constructor of the superclass
        # Additional initialization code for the subclass

    def configure_states(self):
        self.states = ['neutral', 'bullish', 'bearish', 'uncertain', 'trending_up', 'trending_down']
        # self.initial_state = 'neutral'
        self.configure_machine()

    def _identify_bullish_crossover(self,df):
        """
        Identifies bullish crossovers when stoch_rsi_k crosses above stoch_rsi_d.
        Returns a Series where True indicates a bullish crossover.
        """
        # Shift stoch_rsi_k by one to compare previous values with current stoch_rsi_d
        prev_stoch_rsi_k = df['stoch_rsi_k'].shift(1)
        prev_stoch_rsi_d = df['stoch_rsi_d'].shift(1)

        # Bullish crossover condition
        bullish_crossover = (prev_stoch_rsi_k < prev_stoch_rsi_d) & (df['stoch_rsi_k'] > df['stoch_rsi_d'])
        
        return bullish_crossover

    def _identify_bearish_crossover(self,df):
        """
        Identifies bearish crossovers when stoch_rsi_k crosses below stoch_rsi_d.
        Returns a Series where True indicates a bearish crossover.
        """
        # Shift stoch_rsi_k by one to compare previous values with current stoch_rsi_d
        prev_stoch_rsi_k = df['stoch_rsi_k'].shift(1)
        prev_stoch_rsi_d = df['stoch_rsi_d'].shift(1)

        # Bearish crossover condition
        bearish_crossover = (prev_stoch_rsi_k > prev_stoch_rsi_d) & (df['stoch_rsi_k'] < df['stoch_rsi_d'])
        
        return bearish_crossover

    def _identify_oversold(self, df, lower_threshold=0.2):

        # was_oversold = (df['stoch_rsi_k'].shift(1) < lower_threshold) | (df['stoch_rsi_d'].shift(1) < lower_threshold)
        was_oversold = (df['stoch_rsi_k'] < lower_threshold) | (df['stoch_rsi_d'] < lower_threshold)
        return was_oversold
    
    def _identify_overbought(self, df, upper_threshold=0.8):

        # was_overbought = (df['stoch_rsi_k'].shift(1) > upper_threshold) | (df['stoch_rsi_d'].shift(1) > upper_threshold)
        was_overbought = (df['stoch_rsi_k'] > upper_threshold) | (df['stoch_rsi_d'] > upper_threshold)
        return was_overbought
    
    def determine_trend(self, df):
        """
        Determines the trend based on the most recent bullish or bearish crossover.

        Parameters:
        - df: DataFrame with 'bullish_crossover' and 'bearish_crossover' columns.

        Returns:
        - String indicating the trend: 'Bullish', 'Bearish', or 'Neutral'.
        """
        
        df['stoch_rsi_bullish_crossover_threshold'] = df['stoch_rsi_oversold'] & df['stoch_rsi_bullish_crossover']
        df['stoch_rsi_bearish_crossover_threshold'] = df['stoch_rsi_overbought'] & df['stoch_rsi_bearish_crossover']
                
        last_bullish_crossover_index = df[df['stoch_rsi_bullish_crossover']].index.max()
        last_bullish_index = df[df['stoch_rsi_bullish_crossover_threshold']].index.max()
        if last_bullish_index >= last_bullish_crossover_index:
            return 'Bullish'
        
        last_bearish_crossover_index = df[df['stoch_rsi_bearish_crossover']].index.max()
        last_bearish_index = df[df['stoch_rsi_bearish_crossover_threshold']].index.max()
        if last_bearish_index >= last_bearish_crossover_index:
            return 'Bearish'
                    
        # If both crossovers are present, check which one is most recent
        if df['stoch_rsi_bullish_crossover_threshold'].any() and df['stoch_rsi_bearish_crossover_threshold'].any():
            # last_bullish_index = df[df['stoch_rsi_bullish_crossover_threshold']].index.max()
            # last_bearish_index = df[df['stoch_rsi_bearish_crossover_threshold']].index.max()

            if last_bullish_index > last_bearish_index:
                return 'Bullish'
            elif last_bearish_index > last_bullish_index:
                return 'Bearish'
        
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
        pass
        # df['stoch_rsi_bullish_crossover'] = df['stoch_rsi_oversold'] & self._identify_bullish_crossover(df)
        # df['stoch_rsi_bearish_crossover'] = df['stoch_rsi_overbought'] & self._identify_bearish_crossover(df)

    def configure_transitions(self):
        self.machine.add_transition('to_bullish', '*', 'bullish', conditions=['is_bullish'])
        self.machine.add_transition('to_bearish', '*', 'bearish', conditions=['is_bearish'])
        self.machine.add_transition('to_uncertain', '*', 'uncertain', conditions=['is_uncertain'])
        self.machine.add_transition('to_overbought', '*', 'overbought', conditions=['is_overbought'])
        self.machine.add_transition('to_oversold', '*', 'oversold', conditions=['is_oversold'])
        
    def process(self, df):

        try:
            trend = self.determine_trend(df)
            if self.is_bullish(trend):
                if self.state != 'bullish':
                    self.to_bullish()
                
            elif self.is_bearish(trend):
                if self.state != 'bearish':
                    self.to_bearish()
                    
            elif self.is_uncertain(trend):
                if self.state != 'uncertain':
                    self.to_uncertain()

        except Exception as e:
            print(f"An exception occurred: {e}")

    def is_bullish(self, trend):
        return trend == 'Bullish'

    def is_bearish(self, trend):
        return trend == 'Bearish'

    def is_uncertain(self, trend):
        # This might need additional logic to determine 'flat' slope accurately
        return trend == 'Neutral'

    def is_oversold(self, trend):
        return False

    def is_overbought(self, trend):
        return False