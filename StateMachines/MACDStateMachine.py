from pandas import DataFrame, Series
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine
from ta.trend import MACD

class MACDStateMachine(AbstractDataStateMachine):
        
    def configure_states(self):
        self.states = ['neutral', 'bullish_cross', 'bearish_cross']
        # self.initial_state = 'neutral'
        self.configure_machine()

    def enrich_dataset(self, df:DataFrame):
        """
        Identifies bullish and bearish MACD crossovers with the additional condition:
        - Bullish crossovers must occur when both MACD and signal are negative.
        - Bearish crossovers must occur when both MACD and signal are positive.

        Parameters:
        - df: DataFrame which must contain 'close' prices.

        Adds:
        - df['bullish_crossover']: True where a bullish crossover occurs under the conditions.
        - df['bearish_crossover']: True where a bearish crossover occurs under the conditions.
        """
        # Assuming MACD and Signal Line have already been calculated
        df['macd'] = MACD(df['close']).macd()
        df['signal'] = MACD(df['close']).macd_signal()

        # Calculate the difference between MACD and its Signal Line
        df['macd_diff'] = df['macd'] - df['signal']
        df['prev_macd_diff'] = df['macd_diff'].shift(1)

        # Identify bullish crossover with both MACD and signal lines being negative
        df['macd_bullish_crossover'] = ((df['macd_diff'] > 0) & (df['prev_macd_diff'] <= 0)) 
        # Identify bearish crossover with both MACD and signal lines being positive
        df['macd_bearish_crossover'] = ((df['macd_diff'] < 0) & (df['prev_macd_diff'] >= 0)) 
        
        df['macd_positive'] = (df['macd'] > 0) & (df['signal'] > 0)
        df['macd_negative'] = (df['macd'] < 0) & (df['signal'] < 0)
        
        df['macd_bullish_crossover_positive'] = df['macd_bullish_crossover'] & df['macd_negative']
        df['macd_bearish_crossover_negative'] = df['macd_bearish_crossover'] & df['macd_positive']       


    def determine_trend(self, df):
        """
        Finds the most recent crossover type and returns the market situation.

        Parameters:
        - df: DataFrame with 'bullish_crossover' and 'bearish_crossover' columns.

        Returns:
        - A string indicating the market situation: 'bullish', 'bearish', or 'neutral'.
        """
        # Find the last (most recent) bullish and bearish crossovers
        last_bullish_index = df[df['macd_bullish_crossover']].last_valid_index()
        last_bearish_index = df[df['macd_bearish_crossover']].last_valid_index()

        last_bullish_crossover_index = df[df['macd_bullish_crossover_positive']].last_valid_index()
        last_bearish_crossover_index = df[df['macd_bearish_crossover_negative']].last_valid_index()

        # Determine the most recent crossover based on index (row number in the original DataFrame)
        if last_bullish_index is not None and last_bearish_index is not None:
            if last_bullish_index > last_bearish_index: 
                if last_bullish_crossover_index is not None and last_bullish_crossover_index >= last_bullish_index:
                    return 'Bullish'
            else:
                if last_bearish_crossover_index is not None and last_bearish_crossover_index >= last_bearish_index:
                    return 'Bearish'
        elif last_bullish_index is not None:
            if last_bullish_crossover_index is not None and last_bullish_crossover_index >= last_bullish_index:
                return 'Bullish'
        elif last_bearish_index is not None:
            if last_bearish_crossover_index is not None and last_bearish_crossover_index >= last_bearish_index:
                return 'Bearish'
        return 'Neutral'

# Usage example:
# # Assuming 'df' is your DataFrame and it contains 'bullish_crossover' and 'bearish_crossover' columns
# market_situation = find_recent_crossover_status(df)
# print(f"The market situation is {market_situation}.")


    def configure_transitions(self):
        self.machine.add_transition('to_bullish_cross', '*', 'bullish_cross', conditions=['is_bullish_cross'])
        self.machine.add_transition('to_bearish_cross', '*', 'bearish_cross', conditions=['is_bearish_cross'])
        self.machine.add_transition('to_neutral', 'bullish_cross', 'neutral', conditions=['is_neutral_condition'])
        self.machine.add_transition('to_neutral', 'bearish_cross', 'neutral', conditions=['is_neutral_condition'])

    def process(self, df:DataFrame):
        
        try:
            
            trend = self.determine_trend(df)

            # Update conditions based on current and previous values
            if self.is_bullish_cross(trend=trend):
                if self.state != 'bullish_cross':
                    self.to_bullish_cross()
                
            elif self.is_bearish_cross(trend=trend):
                if self.state != 'bearish_cross':
                    self.to_bearish_cross()
                    
            elif self.is_neutral_condition(trend=trend):
                if self.state != 'neutral':
                    self.to_neutral()

        except Exception as e:
            # Handle the case when 'macd' or 'signal' columns are missing in the row
            # Add your exception handling code here
            print(e)

    def is_bullish_cross(self,trend):
        return trend == 'Bullish'

    def is_bearish_cross(self, trend):
        return trend == 'Bearish'

    def is_neutral_condition(self, trend):
        return trend == 'Neutral'
