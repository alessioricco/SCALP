import numpy as np
from pandas import DataFrame, Series
from scipy.stats import linregress
from typing import List
import numpy as np
from pandas import DataFrame, Series
from scipy.stats import linregress

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
    return Series(np.where(np.abs(df[slope_column]) <= tolerance, 'Not trending',
              np.where(df[slope_column] > 0, 'Uptrend', 'Downtrend')))

def calc_change_of_trend(df: DataFrame, trend_column: str) -> None:
    return Series( np.where(df[trend_column].shift() != df[trend_column], 
                                            df[trend_column].shift() + '->' + df[trend_column], 
                                            '')
    )

def last_value(df:DataFrame,column:str):
    return df[column].iloc[-1]



