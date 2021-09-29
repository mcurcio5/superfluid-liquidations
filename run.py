import pandas as pd
from scipy.optimize import bisect
import multiprocessing as mp
import time

from simulation_functions import simulate_and_calculate_pl
from metrics_extraction import calculate_metrics
from data_cleaning_utils import clean_imported_df
from simulation_parameters import sample_params


df = clean_imported_df(pd.read_csv('input_data.csv'))


def calculate_and_return_metrics(refund_rate, params):
    params['refund_rate'] = refund_rate
    local_df = simulate_and_calculate_pl(df, params)
    metrics = calculate_metrics(local_df, params)

    return metrics['liquidator_md_percent'], metrics['liquidator_percent_of_profit']


def calculate_and_return_loss(refund_rate, params):
    liquidator_md, liquidator_percent_of_profit = calculate_and_return_metrics(refund_rate, params)

    return liquidator_md - liquidator_percent_of_profit


def simulate_results(n):
    for i in range(500):
        results = []
        failed_params = []
        for j in range(n):
            params = sample_params()
            params['gas_prediction_ability'] = 0
            try:
                params['refund_rate'] = bisect(calculate_and_return_loss, .00001, .99999, args=params)
            except:
                failed_params.append(params)
                params['refund_rate'] = 0

            local_df = simulate_and_calculate_pl(df, params)
            metrics = calculate_metrics(local_df, params)
            results.append({**params, **metrics})
        result_df = pd.DataFrame(results)
        file_name = 'sim_output/' + str(int(time.time())) + '.csv'
        result_df.to_csv(file_name)


if __name__ == '__main__':
    n_cpus = mp.cpu_count()
    pool = mp.Pool(n_cpus)
    result_ojects = []
    for i in range(n_cpus - 1):
        result = pool.apply_async(simulate_results, (100,))
        result_ojects.append(result)

    results = [result.get() for result in result_ojects]