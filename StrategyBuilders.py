from Strategies.AbstractTradingStrategy import AbstractTradingStrategy
from Strategies.SImpleTradingStrategy import FeatureExtractionStrategy, SimpleTradingStrategy


def buildSimpleTradingStrategy(symbol:str="") -> AbstractTradingStrategy:
    return  SimpleTradingStrategy(symbol)  

def buildFeatureExtractionStrategy(symbol:str="") -> AbstractTradingStrategy:
    return  FeatureExtractionStrategy(symbol)

def getStrategyBuilder(strategy:str)-> AbstractTradingStrategy:
    if strategy == 'SIMPLE':
        return buildSimpleTradingStrategy
    if strategy == 'MODEL':
        return buildFeatureExtractionStrategy