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
        self.machine.add_transition(trigger='sell', source='neutral', dest='sell', conditions=['should_sell'])
        self.machine.add_transition(trigger='sell', source='buy', dest='stop_buy', conditions=['should_sell'])
        self.machine.add_transition(trigger='buy', source='sell', dest='stop_sell', conditions=['should_buy'])
        self.machine.add_transition(trigger='stop_buy', source='stop_buy', dest='neutral', unless=['should_buy'])
        self.machine.add_transition(trigger='stop_sell', source='stop_sell', dest='neutral', unless=['should_sell'])
        self.machine.add_transition(trigger='buy', source='buy', dest='buy', conditions=['should_buy'])
        self.machine.add_transition(trigger='sell', source='sell', dest='sell', conditions=['should_sell'])
        self.machine.add_transition(trigger='stop_sell', source='sell', dest='stop_sell', conditions=['should_stop_sell'])
        self.machine.add_transition(trigger='stop_buy', source='buy', dest='stop_buy', conditions=['should_stop_buy'])

    def should_buy(self):
        return self.strategy.should_buy()

    def should_sell(self):
        return self.strategy.should_sell()

    def should_stop_buy(self):
        return self.strategy.should_stopbuy()

    def should_stop_sell(self):
        return self.strategy.should_stopsell()

    def buy(self):
        """Trigger the transition to buy state if conditions are met."""
        if self.state != 'buy':
            self.trigger('buy')

    def sell(self):
        """Trigger the transition to sell state if conditions are met."""
        if self.state != 'sell':
            self.trigger('sell')

    def stop_buy(self):
        """Transition from buy to stop_buy, eventually moving back to neutral."""
        if self.state != 'stop_buy':
            if self.state == 'buy':
                self.trigger('stop_buy')

    def stop_sell(self):
        """Transition from sell to stop_sell, eventually moving back to neutral."""
        if self.state != 'stop_sell':
            if self.state == 'sell':
                self.trigger('stop_sell')

    def process(self, df:DataFrame):
        self.strategy.process(df)
        
        if self.should_buy():
            self.buy()
        elif self.should_sell():
            self.sell()
        elif self.should_stop_sell():
            self.stop_sell()
        elif self.should_stop_buy():
            self.stop_buy()
        
        

