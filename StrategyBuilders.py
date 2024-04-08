from StateMachines.HullMovingAverageStateMachine import HullMovingAverageStateMachine
from StateMachines.MACDStateMachine import MACDStateMachine
from StateMachines.StochasticRSIStateMachine import StochasticRSIStateMachine
from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
# from Strategies.MacdStochTradingStrategy import MacdStochRSITradingStrategy
from Strategies.SImpleTradingStrategy import SimpleTradingStrategy
from Strategies.StochRSITradingStrategy import StochRSITradingStrategy


# def buildMacdStochRSITradingStrategy(symbol:str="") -> AbstractTradingStrategy:
#     macd_sm = MACDStateMachine()
#     stochastic_sm = StochasticRSIStateMachine()
#     strategy:AbstractTradingStrategy = MacdStochRSITradingStrategy(symbol, macd_sm, stochastic_sm)  
#     return strategy

def buildStochRSITradingStrategy(symbol:str="") -> AbstractTradingStrategy:
    stochastic_sm = StochasticRSIStateMachine()
    hma_sm = HullMovingAverageStateMachine()
    macd_sm = MACDStateMachine()
    strategy:AbstractTradingStrategy = StochRSITradingStrategy(symbol, stochastic_sm, hma_sm, macd_sm)  
    return strategy

def buildSimpleTradingStrategy(symbol:str="") -> AbstractTradingStrategy:
    return  SimpleTradingStrategy(symbol)  
    # return strategy

def getStrategyBuilder(strategy:str)-> AbstractTradingStrategy:
    # if strategy == 'MACDSTOCHRSI':
    #     return buildMacdStochRSITradingStrategy
    if strategy == 'SIMPLE':
        return buildSimpleTradingStrategy
    elif strategy == 'STOCHRSI':
        return buildStochRSITradingStrategy
    
    # else:
    #     return buildMacdStochRSITradingStrategy