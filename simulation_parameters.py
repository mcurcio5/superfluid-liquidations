########
# These functions provide defaults for simulation parameters
########

import pandas as pd
import numpy as np
from numpy.random import default_rng

rng = default_rng()

pd.options.mode.chained_assignment = None

LOGUNIFORM_PARAM_RANGES = {
    'upfront_fee': [0.002, .05],
    'monthly_opened_streams': [100, 10000],
    'average_stream_lifetime': [3, 250],  # days
    'percent_accidently_liquidated_per_month': [0.2, 60],  # on accident
    'average_stream_size': [100, 10000]  # if higher... then that's success
}

UNIFORM_PARAM_RANGES = {
    'upfront_hours': [0, 20],
    'refund_rate': [0, 1],
    'min_self_liquidation_savings': [2, 50],  # implicit premium for letting protocol liquidate
    'gas_prediction_ability': [0, 2],  # n hours ahead the liquidator has perfect gas price info
    'lowest_stream_cost_ratio': [.8, 4],  # lowest monthly stream / stream cost user opens under
}


def sample_params():
    """ samples param space randomly """
    loguniform_params = {p: rng.uniform(LOGUNIFORM_PARAM_RANGES[p][0], LOGUNIFORM_PARAM_RANGES[p][1]) for p in
                         LOGUNIFORM_PARAM_RANGES}
    uniform_params = {p: rng.uniform(UNIFORM_PARAM_RANGES[p][0], UNIFORM_PARAM_RANGES[p][1]) for p in
                      UNIFORM_PARAM_RANGES}

    return {**loguniform_params, **uniform_params}
