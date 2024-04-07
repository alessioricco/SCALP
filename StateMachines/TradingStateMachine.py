from pandas import DataFrame
from StateMachines.AbstractDataStateMachine import AbstractDataStateMachine
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy

class TradingStateMachine(AbstractDataStateMachine):
    def __init__(self, strategy: AbstractTradingStrategy):
        self._strategy = strategy
        super().__init__()

    @property
    def strategy(self):
        return self._strategy

    def configure_states(self):
        self.states = ['neutral', 'buy', 'sell', 'stop_buy', 'stop_sell']
        # self.initial_state = 'neutral'
        self.configure_machine()

    def enrich_dataset(self, df:DataFrame):
        pass

    def configure_transitions(self):
        self.machine.add_transition(trigger='buy', source='neutral', dest='buy', conditions=['should_buy'])
        self.machine.add_transition(trigger='stop_buy', source='buy', dest='stop_buy', conditions=['should_stop_buy'])
        self.machine.add_transition(trigger='to_neutral_from_stop_buy', source='stop_buy', dest='neutral', unless=['should_buy'])

        self.machine.add_transition(trigger='sell', source='neutral', dest='sell', conditions=['should_sell'])
        self.machine.add_transition(trigger='stop_sell', source='sell', dest='stop_sell', conditions=['should_stop_sell'])
        self.machine.add_transition(trigger='to_neutral_from_stop_sell', source='stop_sell', dest='neutral', unless=['should_sell'])

        # Optional: Direct transition back to neutral if conditions are immediately met
        self.machine.add_transition(trigger='reset_to_neutral', source=['buy', 'sell', 'stop_buy', 'stop_sell'], dest='neutral', conditions=['should_reset'])
        

    def should_buy(self):
        return self.strategy.should_buy()

    def should_sell(self):
        return self.strategy.should_sell()

    def should_stop_buy(self):
        return self.strategy.should_stopbuy()

    def should_stop_sell(self):
        return self.strategy.should_stopsell()

    def should_reset(self):
        return self.state in ['stop_buy', 'stop_sell']

    def to_buy(self):
        """Attempt to transition to the Buy state if conditions are met."""
        if self.state == 'neutral' and self.should_buy():
            self.trigger('buy')

    def to_stop_buy(self):
        """Attempt to transition to the Stop Buy state if conditions are met."""
        if self.state == 'buy' and self.should_stop_buy():
            self.trigger('stop_buy')

    def to_sell(self):
        """Attempt to transition to the Sell state if conditions are met."""
        if self.state == 'neutral' and self.should_sell():
            self.trigger('sell')

    def to_stop_sell(self):
        """Attempt to transition to the Stop Sell state if conditions are met."""
        if self.state == 'sell' and self.should_stop_sell():
            self.trigger('stop_sell')

    def to_neutral(self):
        """Checks conditions and transitions to Neutral if applicable. This can be from any state."""
        if self.state in ['buy', 'sell', 'stop_buy', 'stop_sell']:
            if self.should_reset():
                self.trigger('reset_to_neutral')
            elif self.state == 'stop_buy' and not self.should_buy():
                self.trigger('to_neutral_from_stop_buy')
            elif self.state == 'stop_sell' and not self.should_sell():
                self.trigger('to_neutral_from_stop_sell')

        
    def process(self, df: DataFrame):
        """
        Processes the given DataFrame using the trading strategy to determine state transitions.

        Parameters:
        - df: DataFrame containing market data.
        """
        # Step 1: Process the market data with the strategy.
        self.strategy.process(df)

        # Step 2: Determine the next state based on strategy conditions.
        # The order of these checks is important to ensure logical flow and precedence of states.
        
        # Attempt to transition to buy if in neutral and conditions are met.
        if self.state == 'neutral' and self.should_buy():
            self.to_buy()
            return  # Return after a successful transition to avoid conflicting actions.

        # Attempt to transition to sell if in neutral and conditions are met.
        if self.state == 'neutral' and self.should_sell():
            self.to_sell()
            return  # Return after a successful transition to avoid conflicting actions.

        # If currently buying and conditions to stop buying are met, transition to stop buy.
        if self.state == 'buy' and self.should_stop_buy():
            self.to_stop_buy()
            return  # Return after a successful transition to avoid conflicting actions.

        # If currently selling and conditions to stop selling are met, transition to stop sell.
        if self.state == 'sell' and self.should_stop_sell():
            self.to_stop_sell()
            return  # Return after a successful transition to avoid conflicting actions.

        # If in stop buy or stop sell, check if it's time to go back to neutral.
        # This could be based on a specific reset condition or simply not meeting the buy/sell conditions anymore.
        if self.state in ['stop_buy', 'stop_sell']:
            self.to_neutral()
            return  # Return after checking to avoid conflicting actions.

        # If none of the above conditions are met, it might indicate a situation where the strategy
        # doesn't suggest any immediate action, or the current state remains the best option.

