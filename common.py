# from scipy.stats import linregress

# def calculate_slope(series):
#     # Calculate the slope of the linear regression line
#     regression = linregress(range(len(series)), series)
#     return regression.slope

# # Apply the slope calculation over a rolling window
# window = 20  # Define the window for trend analysis
# df['Slope'] = df['Close'].rolling(window=window).apply(calculate_slope, raw=True)

# # Determine the trend based on the slope
# df['Trend'] = np.where(df['Slope'] > 0, 'Uptrend',
#               np.where(df['Slope'] < 0, 'Downtrend', 'Not trending'))
