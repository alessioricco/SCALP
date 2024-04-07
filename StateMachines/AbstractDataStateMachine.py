# Required Libraries
from abc import ABC, abstractmethod
from transitions import Machine
import pandas as pd
from rich.console import Console
console = Console()

class AbstractDataStateMachine(ABC):
    def __init__(self, initial_state='neutral'):
        self.states = []
        self.initial_state = initial_state
        # Ensure subclasses have defined their states and transitions before configuring the machine
        self.configure_states()
        self.configure_transitions()
        self.configure_machine()

    @abstractmethod
    def enrich_dataset(self, df:pd.DataFrame):
        pass

    def configure_machine(self):
        # Now the machine is configured after states and transitions have been defined by the subclass
        self.machine = Machine(model=self, states=self.states, initial=self.initial_state, after_state_change='_after_state_change')
    
    def getCurrentState(self):
        return self.state
    
    @abstractmethod
    def configure_states(self):
        """Subclasses should define their specific states here."""
        pass

    @abstractmethod
    def configure_transitions(self):
        """Subclasses should define their specific transitions here."""
        pass

    @abstractmethod
    def process(self, df:pd.DataFrame):
        """Defines how each row of data is processed, to be implemented by subclasses."""
        pass

    def _after_state_change(self):
        """A callback executed after each state change."""
        # console.print(f"[italic]{self.__class__.__name__} transitioned to {self.state}[/italic]")
        pass

