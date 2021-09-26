import pandas as pd
from simulation_functions import simulate_and_calculate_n_times
from data_cleaning_utils import clean_imported_df

if __name__ == '__main__':
    df = clean_imported_df(pd.read_csv('input_data.csv'))
    i = 0
    while i < 1000:
        output = simulate_and_calculate_n_times(df, 10000)
        output.to_csv('./output/' + str(i) + '.csv')
        i += 1
