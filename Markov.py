import pandas as pd



def read_transition_matrix():
    global transition_matrix
    return pd.read_csv('./transition_matrix.csv', index_col=0)


def get_transition_probability(current_pattern, next_pattern, matrix):
    if current_pattern in matrix.index and next_pattern in matrix.columns:
        return matrix.at[current_pattern, next_pattern]
    else:
        return 0  # Return 0 probability if the pattern hasn't been observed
    
def bet(current_pattern, transition_matrix):
    # Calculate the probability of transitioning to each possible state
    probabilities = transition_matrix.loc[current_pattern]
    # Bet on the state with the highest probability
    return probabilities.idxmax()

def predict_N_steps_ahead(current_pattern, transition_matrix, steps=2):
    # Check if the current pattern exists in the transition matrix
    if current_pattern not in transition_matrix.index:
        return "Current pattern not found in the matrix"

    # Step through the matrix to find the most probable states over the specified number of steps
    next_pattern = current_pattern
    for _ in range(steps):
        next_pattern = transition_matrix.loc[next_pattern].idxmax()  # Get the next pattern with the highest probability

        # Ensure the next pattern is a valid entry in the matrix for subsequent steps
        if pd.isna(next_pattern) or next_pattern not in transition_matrix.index:
            return "Transition leads to an unknown pattern"
    
    return next_pattern

def define_candle_color(row):
    """Define the color of the candle based on open and close prices."""
    if row['close'] > row['open']:
        return 'G'  # Green
    else:
        return 'R'  # Red

def last_five_candle_pattern(df):
    """Generate the pattern string for the last five candles."""
    # Check if the DataFrame has at least 5 rows
    if len(df) < 5:
        raise ValueError("DataFrame must contain at least 5 rows of candle data to generate a pattern.")
    
    # Apply the function to determine the candle color for each row
    df['state'] = df.apply(define_candle_color, axis=1)
    
    # Extract the last five 'state' values and join them into a single string
    pattern = ''.join(df['state'].tail(5))
    return pattern