import numpy as np
from pandas import DataFrame, Series
from scipy.stats import linregress
from typing import List
import numpy as np
from pandas import DataFrame, Series
from scipy.stats import linregress
from pandas import DataFrame, Series
import numpy as np

SELL = -1
BUY = 1
HOLD = 0

UPTREND = 1
NEUTRAL = 0
DOWNTREND = -1

def _calculate_slope(series: List[float]) -> float:
    # Calculate the slope of the linear regression line
    regression = linregress(range(len(series)), series)
    return regression.slope

# Apply the slope calculation over a rolling window
def calc_slope(df:DataFrame,value_column:str="close",window=10)->Series:
    # window = 20  # Define the window for trend analysis
    return df[value_column].rolling(window=window).apply(_calculate_slope, raw=True)

def calc_trend(df:DataFrame,slope_column:str,tolerance=0.0001)->Series:
    # Determine the trend based on the slope
    #  -1 downtrend
    #  0 not trending
    #  1 uptrend
    s = Series(np.where(np.abs(df[slope_column]) <= tolerance, 0,
              np.where(df[slope_column] > 0, 1, -1)))
    return s

def calc_change_of_trend(df: DataFrame, trend_column: str) -> Series:
    return Series(np.where(df[trend_column].shift() != df[trend_column], True, False))

def last_value(df:DataFrame,column:str):
    return df[column].iloc[-1]


def weighted_moving_average(data, period):
    weights = np.arange(1, period + 1)  # Weighting factors
    return data.rolling(window=period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def hull_moving_average(data, period):
    half_period_wma = weighted_moving_average(data, period // 2)
    full_period_wma = weighted_moving_average(data, period)
    raw_hma = 2 * half_period_wma - full_period_wma
    hma = weighted_moving_average(raw_hma, int(np.sqrt(period)))  # Final HMA calculation
    return hma


