class TradingStrategy:
    def start_condition(self, data):
        """Determine whether to start a trade based on the given data."""
        raise NotImplementedError

    def stop_condition(self, data):
        """Determine whether to stop a trade based on the given data."""
        raise NotImplementedError


class MACDStrategy(TradingStrategy):
    def start_condition(self, data):
        macd, signal = data['macd'], data['signal']
        return macd[-1] > signal[-1] and macd[-2] <= signal[-2]

    def stop_condition(self, data):
        macd, signal = data['macd'], data['signal']
        return macd[-1] < signal[-1]

class RSIStrategy(TradingStrategy):
    def start_condition(self, data):
        rsi = data['rsi']
        return rsi[-1] < 30  # Oversold condition

    def stop_condition(self, data):
        rsi = data['rsi']
        return rsi[-1] > 70  # Overbought condition

