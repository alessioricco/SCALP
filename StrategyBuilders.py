from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from Strategies.SImpleTradingStrategy import SimpleTradingStrategy


def buildSimpleTradingStrategy(symbol:str="") -> AbstractTradingStrategy:
    return  SimpleTradingStrategy(symbol)  

def getStrategyBuilder(strategy:str)-> AbstractTradingStrategy:
    if strategy == 'SIMPLE':
        return buildSimpleTradingStrategy
