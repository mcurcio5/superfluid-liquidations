####
# functions to extract metrics from Superfluid simulation runs
####

import pandas as pd
import numpy as np


def calculate_max_drawdown(values):
    """ returns max drawdown value and time for drawdown to occur """
    maxes = np.maximum.accumulate(values)
    drawdowns = maxes - values
    drawdown_end_index = np.argmax(drawdowns)
    drawdown_start_index = 0 if drawdown_end_index == 0 else np.argmax(values[:drawdown_end_index])

    return values[drawdown_start_index] - values[drawdown_end_index]


def calculate_metrics(df, params):
    """ calculates max drawdown, time to max drawdown and P&Ls """
    liquidator_pl_cumsum = np.array(df['liquidator_pl'].cumsum())
    gas_tank_usd_pl_cumsum = np.array(df['gas_tank_eth_pl'].cumsum() * np.mean(df['price']))

    total_profit = liquidator_pl_cumsum[-1] + gas_tank_usd_pl_cumsum[-1]

    liquidator_md = calculate_max_drawdown(liquidator_pl_cumsum)
    gas_tank_md = calculate_max_drawdown(gas_tank_usd_pl_cumsum)
    liquidator_md_percent = liquidator_md / (liquidator_md + gas_tank_md)
    liquidator_percent_of_profit = liquidator_pl_cumsum[-1] / total_profit

    n_opened = np.sum(df['n_opened'])
    n_streams_self_closed = np.sum(df['n_self_closed'])
    n_streams_liquidated = np.sum(df['n_liquidated'])
    percent_self_closed = n_streams_self_closed / (n_streams_self_closed + n_streams_liquidated)
    percent_closed = (n_streams_self_closed + n_streams_liquidated) / n_opened

    return {
        'liquidator_md': liquidator_md,
        'gas_tank_md': gas_tank_md,
        'liquidator_md_percent': liquidator_md_percent,
        'liquidator_percent_of_profit': liquidator_percent_of_profit,
        'total_profit': total_profit,
        'n_opened': np.sum(df['n_opened']),
        'percent_self_closed': percent_self_closed,
        'percent_closed': percent_closed,
        'total_margin_taken': np.sum(df['n_liquidated'] * df['avg_liquidation_size']),
    }