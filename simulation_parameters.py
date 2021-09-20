########
# These functions provide defaults for simulation parameters
########

import pandas as pd
import numpy as np
from numpy.random import default_rng

rng = default_rng()

pd.options.mode.chained_assignment = None

LOGUNIFORM_PARAM_RANGES = {'upfront_fee': [0, .1],
                           'monthly_opened_streams': [100, 1000],
                           'average_stream_lifetime': [5, 365],  # days
                           'percent_accidently_liquidated_per_month': [0.1, 30],  # on accident
                           'average_stream_size': [10, 10000],  # if higher... then that's success
                           'liquidator_capital': [1000, 100000]}

UNIFORM_PARAM_RANGES = {'upfront_hours': [0, 24],
                        'refund_rate': [0, 1],
                        'gas_tank_size': [1, 500],
                        'max_days_to_return': [5, 200],
                        'max_liquidation_wait_time': [0, 48],
                        'min_self_liquidation_savings': [0, 20],  # implicit premium for letting protocol liquidate
                        'gas_prediction_ability': [0, 2]}  # number of hours the liquidator can predict gas prices


def sample_params():
    """ samples param space randomly """
    loguniform_params = {p: rng.uniform(LOGUNIFORM_PARAM_RANGES[p][0], LOGUNIFORM_PARAM_RANGES[p][1]) for p in
                         LOGUNIFORM_PARAM_RANGES}
    uniform_params = {p: rng.uniform(UNIFORM_PARAM_RANGES[p][0], UNIFORM_PARAM_RANGES[p][1]) for p in
                      UNIFORM_PARAM_RANGES}

    return {**loguniform_params, **uniform_params}
