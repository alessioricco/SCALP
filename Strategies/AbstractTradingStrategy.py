from abc import ABC, abstractmethod
import datetime
from pandas import DataFrame
from rich.console import Console
from ta.momentum import StochRSIIndicator
from ta.trend import MACD
import common
import yaml
import networkx as nx


console = Console()
class AbstractTradingStrategy(ABC):
    
    def __init__(self, symbol=''):
        self.last_printed_value = {}
        self.symbol = symbol
        self.last_close = 0
        self.max_price = 0
        self.min_price = 0  
        self.feature_calculations = {
            'stoch_rsi': self.calc_stoch_rsi,
            'stoch_rsi_k': self.calc_stoch_rsi_k,
            'stoch_rsi_d': self.calc_stoch_rsi_d,
            'stoch_rsi_overbought_': self.calc_stoch_rsi_overbought,
            'stoch_rsi_oversold_': self.calc_stoch_rsi_oversold,
            'stoch_rsi_bullish_crossover_': self.calc_stoch_rsi_bullish_crossover,
            'stoch_rsi_bearish_crossover_': self.calc_stoch_rsi_bearish_crossover,
            'stoch_rsi_slope': self.calc_stoch_rsi_slope,
            'stoch_rsi_k_slope': self.calc_stoch_rsi_k_slope,
            'stoch_rsi_d_slope': self.calc_stoch_rsi_d_slope,
            'stoch_rsi_trend_': self.calc_stoch_rsi_trend,
            'stoch_rsi_change_of_trend_': self.calc_stoch_rsi_change_of_trend,
            f'{self.hma_column}': self.calc_hma,
            f'{self.hma_column}_slope': self.calc_hma_slope,
            f'{self.hma_column}_trend_': self.calc_hma_trend,
            f'{self.hma_column}_change_of_trend_': self.calc_hma_change_of_trend,
            f'{self.hma_column}_above_price_': self.calc_hma_above_price,
            'macd': self.calc_macd,
            'macd_signal': self.calc_macd_signal,
            'macd_diff': self.calc_macd_diff,
            'prev_macd_diff': self.calc_prev_macd_diff,
            'macd_bullish_crossover_': self.calc_macd_bullish_crossover,
            'macd_bearish_crossover_': self.calc_macd_bearish_crossover,
            'macd_positive_': self.calc_macd_positive,
            'macd_slope': self.calc_macd_slope,
            'macd_signal_slope': self.calc_macd_signal_slope,
            'macd_trend_': self.calc_macd_trend,
            'macd_change_of_trend_': self.calc_macd_change_of_trend
        }
        
    def print_no_repeat(self, key, value, now=datetime.datetime.now(datetime.UTC)):
        # asyncio.run(self.print_no_repeat_async(key, value))
        if key not in self.last_printed_value:
            self.last_printed_value[key] = None
        if value != self.last_printed_value[key]:
            # now = datetime.datetime.now(datetime.UTC)
            console.print(f"{now} | {self.symbol} | {value}")
            # print(value)
            self.last_printed_value[key] = value    
    
    async def print_no_repeat_async(self, key, value,now):
        self.print_no_repeat(key, value, now)    
    
    def getSymbolAndTimeFrame(self):
        return self.symbol
    
    @staticmethod
    def get_features_list(df:DataFrame):
        return [x for x in df.columns if x[-1] == "_"]
    
    def _compute_required_columns(self, columns, filename="./dependencies.yml"):
        """
        Given a list of column names and a YAML file with dependencies,
        return all required columns to be computed, including dependencies,
        sorted by the order of dependency.

        :param columns: A list of initial column names.
        :param filename: The YAML file containing the dependency map.
        :return: A list of column names sorted by dependencies.
        """
        
        def _add_edges(graph, columns, dependency_map):
            """
            Recursively add edges to the graph based on dependencies.

            :param graph: Directed graph object.
            :param columns: A list of column names.
            :param dependency_map: A dictionary mapping each column to its dependencies.
            """
            for column in columns:
                if column in dependency_map and 'depends' in dependency_map[column]:
                    for dependency in dependency_map[column]['depends']:
                        graph.add_edge(dependency, column)
                        _add_edges(graph, [dependency], dependency_map)
        
        # Load the dependency map from the YAML file
        with open(filename, 'r') as file:
            dependency_map = yaml.load(file, Loader=yaml.FullLoader)['columns']
        
        # Create a directed graph
        dependency_graph = nx.DiGraph()
        
        # Add nodes and edges for all columns including those that are not dependencies
        all_columns = set(columns) | set(dependency_map.keys())
        dependency_graph.add_nodes_from(all_columns)
        _add_edges(dependency_graph, columns, dependency_map)
        
        # Perform topological sort to determine the order of computation
        try:
            sorted_columns = list(nx.topological_sort(dependency_graph))
            # Filter sorted columns to ensure only those needed are included
            needed_columns = set(columns)
            for column in reversed(sorted_columns):
                if column in needed_columns:
                    needed_columns.update(dependency_map.get(column, {}).get('depends', []))
            return [col for col in sorted_columns if col in needed_columns]
        except nx.NetworkXUnfeasible:
            raise ValueError("A cyclic dependency occurred in the columns, check the dependency map.")

    def _calc_stoch_rsi_bullish_crossover(self,df:DataFrame):
        """
        Identifies bullish crossovers when stoch_rsi_k crosses above stoch_rsi_d.
        Returns a Series where True indicates a bullish crossover.
        """
        # Shift stoch_rsi_k by one to compare previous values with current stoch_rsi_d
        prev_stoch_rsi_k = df['stoch_rsi_k'].shift(1)
        prev_stoch_rsi_d = df['stoch_rsi_d'].shift(1)

        # Bullish crossover condition
        bottom = ((prev_stoch_rsi_k == 0) & (prev_stoch_rsi_d == 0)) & ((df['stoch_rsi_k'] > 0) | (df['stoch_rsi_d'] > 0))

        return bottom | ((prev_stoch_rsi_k < prev_stoch_rsi_d) & (df['stoch_rsi_k'] > df['stoch_rsi_d']))
        
    def _calc_stoch_rsi_bearish_crossover(self,df:DataFrame):
        """
        Identifies bearish crossovers when stoch_rsi_k crosses below stoch_rsi_d.
        Returns a Series where True indicates a bearish crossover.
        """
        # Shift stoch_rsi_k by one to compare previous values with current stoch_rsi_d
        prev_stoch_rsi_k = df['stoch_rsi_k'].shift(1)
        prev_stoch_rsi_d = df['stoch_rsi_d'].shift(1)

        # Bearish crossover condition
        top =  ((prev_stoch_rsi_k == 1) & (prev_stoch_rsi_d == 1)) & ((df['stoch_rsi_k'] < 1) | (df['stoch_rsi_d'] < 1))
        return top | ((prev_stoch_rsi_k > prev_stoch_rsi_d) & (df['stoch_rsi_k'] < df['stoch_rsi_d'])) 

    def _calc_stoch_rsi_oversold(self, df:DataFrame, lower_threshold=0.4):

        return (df['stoch_rsi_k'] < lower_threshold) & (df['stoch_rsi_d'] < lower_threshold) #| ((df['stoch_rsi_k'] == 0) & (df['stoch_rsi_d'] == 0)))
    
    def _calc_stoch_rsi_overbought(self, df:DataFrame, upper_threshold=0.6):

        return (df['stoch_rsi_k'] > upper_threshold) & (df['stoch_rsi_d'] > upper_threshold)

    def calc_stoch_rsi(self, df):
        df['stoch_rsi'] = StochRSIIndicator(df['close']).stochrsi()

    def calc_stoch_rsi_k(self, df):
        df['stoch_rsi_k'] = StochRSIIndicator(df['close']).stochrsi_k()

    def calc_stoch_rsi_d(self, df):
        df['stoch_rsi_d'] = StochRSIIndicator(df['close']).stochrsi_d()

    def calc_stoch_rsi_overbought(self, df):
        df['stoch_rsi_overbought_'] = self._calc_stoch_rsi_overbought(df)

    def calc_stoch_rsi_oversold(self, df):
        df['stoch_rsi_oversold_'] = self._calc_stoch_rsi_oversold(df)

    def calc_stoch_rsi_bullish_crossover(self, df):
        df['stoch_rsi_bullish_crossover_'] = self._calc_stoch_rsi_bullish_crossover(df)

    def calc_stoch_rsi_bearish_crossover(self, df):
        df['stoch_rsi_bearish_crossover_'] = self._calc_stoch_rsi_bearish_crossover(df)

    def calc_stoch_rsi_slope(self, df):
        df['stoch_rsi_slope'] = common.calc_slope(df, 'stoch_rsi')

    def calc_stoch_rsi_k_slope(self, df):
        df['stoch_rsi_k_slope'] = common.calc_slope(df, 'stoch_rsi_k')

    def calc_stoch_rsi_d_slope(self, df):
        df['stoch_rsi_d_slope'] = common.calc_slope(df, 'stoch_rsi_d')

    def calc_stoch_rsi_trend(self, df):
        df['stoch_rsi_trend_'] = common.calc_trend(df, 'stoch_rsi_slope')

    def calc_stoch_rsi_change_of_trend(self, df):
        df['stoch_rsi_change_of_trend_'] = common.calc_change_of_trend(df, 'stoch_rsi_trend_')

    def calc_hma(self, df):
        df[self.hma_column] = common.hull_moving_average(df['close'], self.hma_period)

    def calc_hma_slope(self, df):
        df[f'{self.hma_column}_slope'] = common.calc_slope(df, self.hma_column)

    def calc_hma_trend(self, df):
        df[f'{self.hma_column}_trend_'] = common.calc_trend(df, f'{self.hma_column}_slope')

    def calc_hma_change_of_trend(self, df):
        df[f'{self.hma_column}_change_of_trend_'] = common.calc_change_of_trend(df, f'{self.hma_column}_trend_')

    def calc_hma_above_price(self, df):
        df[f'{self.hma_column}_above_price_'] = df[self.hma_column] > df['close']

    def calc_macd(self, df):
        df['macd'] = MACD(df['close'],5,13,9).macd()

    def calc_macd_signal(self, df):
        df['macd_signal'] = MACD(df['close'],5,13,9).macd_signal()

    def calc_macd_diff(self, df):
        df['macd_diff'] = MACD(df['close'],5,13,9).macd_diff()

    def calc_prev_macd_diff(self, df):
        df['prev_macd_diff'] = df['macd_diff'].shift(1)

    def calc_macd_bullish_crossover(self, df):
        df['macd_bullish_crossover_'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        # df['Bullish_Crossover'] = np.where((df['MACD'] > df['Signal_Line']) & (df['MACD'].shift(1) <= df['Signal_Line'].shift(1)), True, False)

    def calc_macd_bearish_crossover(self, df):
        df['macd_bearish_crossover_'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        # df['Bearish_Crossover'] = np.where((df['MACD'] < df['Signal_Line']) & (df['MACD'].shift(1) >= df['Signal_Line'].shift(1)), True, False)

    def calc_macd_positive(self, df):
        df['macd_positive_'] = df['macd_diff'] >= 0

    def calc_macd_slope(self, df):
        df['macd_slope'] = common.calc_slope(df, 'macd')

    def calc_macd_signal_slope(self, df):
        df['macd_signal_slope'] = common.calc_slope(df, 'macd_signal')

    def calc_macd_trend(self, df):
        df['macd_trend_'] = common.calc_trend(df, 'macd_slope')

    def calc_macd_change_of_trend(self, df):
        df['macd_change_of_trend_'] = common.calc_change_of_trend(df, 'macd_trend_')

    def last_value_of(self,df:DataFrame,column:str):
        return df[column].iloc[-1]

    def last_row_of(self,df:DataFrame):
        return df.iloc[-1].to_dict()    
    
    @abstractmethod
    def enrich_dataset(self, df:DataFrame):
        """Determines whether to execute a sell based on indicator states."""
        pass    
    
    @abstractmethod
    def should_buy(self):
        """Determines whether to execute a buy based on indicator states."""
        pass

    @abstractmethod
    def should_sell(self):
        """Determines whether to execute a sell based on indicator states."""
        pass

    @abstractmethod
    def should_stopbuy(self):
        """Determines whether to stop buying based on indicator states."""
        pass

    @abstractmethod
    def should_stopsell(self):
        """Determines whether to stop selling based on indicator states."""
        pass

    @abstractmethod
    def process(self, df:DataFrame, balance:float):
        """Determines whether to execute a sell based on indicator states."""
        pass

