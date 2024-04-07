from StateMachines.HullMovingAverageStateMachine import HullMovingAverageStateMachine
from StateMachines.MACDStateMachine import MACDStateMachine
from StateMachines.StochasticRSIStateMachine import StochasticRSIStateMachine
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from Strategies.MacdStochTradingStrategy import MacdStochRSITradingStrategy
from Strategies.StochRSITradingStrategy import StochRSITradingStrategy


def buildMacdStochRSITradingStrategy(symbol:str="") -> AbstractTradingStrategy:
    macd_sm = MACDStateMachine()
    stochastic_sm = StochasticRSIStateMachine()
    strategy:AbstractTradingStrategy = MacdStochRSITradingStrategy(symbol, macd_sm, stochastic_sm)  
    return strategy

def buildStochRSITradingStrategy(symbol:str="") -> AbstractTradingStrategy:
    stochastic_sm = StochasticRSIStateMachine()
    hma_sm = HullMovingAverageStateMachine()
    macd_sm = MACDStateMachine()
    strategy:AbstractTradingStrategy = StochRSITradingStrategy(symbol, stochastic_sm, hma_sm, macd_sm)  
    return strategy

def getStrategyBuilder(strategy:str):
    if strategy == 'MACDSTOCHRSI':
        return buildMacdStochRSITradingStrategy
    elif strategy == 'STOCHRSI':
        return buildStochRSITradingStrategy
    else:
        return buildMacdStochRSITradingStrategy