########
# These functions provide defaults for simulation parameters
########

import pandas as pd
import numpy as np
from numpy.random import default_rng

rng = default_rng()

pd.options.mode.chained_assignment = None

N_CORE_PARAMS = 5
FEES = np.exp(np.linspace(np.log(.002), np.log(.05), N_CORE_PARAMS))
HOURS = np.linspace(20, 0, N_CORE_PARAMS)
CORE_PARAMS = [{'upfront_fee': a, 'upfront_hours': b} for a, b in list(zip(FEES, HOURS))]

LOGUNIFORM_PARAM_RANGES = {
    'monthly_opened_streams': [100, 10000],
    'average_stream_lifetime': [3, 250],  # days
    'percent_accidently_liquidated_per_month': [0.2, 60],  # on accident
    'average_stream_size': [100, 10000]  # if higher... then that's success
}

UNIFORM_PARAM_RANGES = {
    'refund_rate': [0, 1],
    'min_self_liquidation_savings': [2, 50],  # implicit premium for letting protocol liquidate
    'gas_prediction_ability': [0, 2],  # n hours ahead the liquidator has perfect gas price info
    'lowest_stream_cost_ratio': [.8, 4],  # lowest monthly stream / stream cost user opens under
    'distribution_inverse_skewness': [.8, 5]  # sets the gamma_k variable, lowest value most skew
}


def sample_params():
    """ samples param space randomly """
    core_params = np.random.choice(CORE_PARAMS)
    loguniform_params = {p: np.exp(rng.uniform(np.log(LOGUNIFORM_PARAM_RANGES[p][0] + .0001),
                                               np.log(LOGUNIFORM_PARAM_RANGES[p][1] + .0001))) for p in
                         LOGUNIFORM_PARAM_RANGES}

    uniform_params = {p: rng.uniform(UNIFORM_PARAM_RANGES[p][0],
                                     UNIFORM_PARAM_RANGES[p][1]) for p in UNIFORM_PARAM_RANGES}

    return {**core_params, **loguniform_params, **uniform_params}
