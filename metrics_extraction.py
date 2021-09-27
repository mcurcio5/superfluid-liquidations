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

    return values[drawdown_start_index] - values[drawdown_end_index], drawdown_end_index - drawdown_start_index


def calculate_metrics(df, params):
    """ calculates max drawdown, time to max drawdown and P&Ls """
    liquidator_pl_cumsum = np.array(df['liquidator_pl'].cumsum())
    gas_tank_eth_pl_cumsum = np.array(df['gas_tank_eth_pl'].cumsum())

    liquidator_md, liquidator_md_time = calculate_max_drawdown(liquidator_pl_cumsum)
    gas_tank_md, gas_tank_md_time = calculate_max_drawdown(gas_tank_eth_pl_cumsum)

    n_streams_self_closed = np.sum(df['n_self_closed'])
    n_streams_liquidated = np.sum(df['n_liquidated'])
    percent_self_closed = n_streams_self_closed / (n_streams_self_closed + n_streams_liquidated)

    n_opened = np.sum(df['n_opened'])
    percent_closed = (n_streams_self_closed + n_streams_liquidated) / n_opened
    gas_tank_usd_fees = np.sum(df['n_opened'] * df['price'] * params['upfront_fee'])
    gas_refunded_usd = np.sum(df['gas_refunded_eth'] * df['price'])

    gas_tank_realized_pl = gas_tank_usd_fees * percent_closed - gas_refunded_usd  # pl that only includes closed txs
    percent_pl_to_liquidator = liquidator_pl_cumsum[-1] / (gas_tank_realized_pl + liquidator_pl_cumsum[-1])

    return {
        'liquidator_md': liquidator_md,
        'liquidator_md_time': liquidator_md_time,
        'liquidator_pl': liquidator_pl_cumsum[-1],
        'gas_tank_md': gas_tank_md,
        'gas_tank_md_time': gas_tank_md_time,
        'gas_tank_eth_pl': gas_tank_eth_pl_cumsum[-1],
        'gas_tank_usd_pl': np.sum(df['gas_tank_usd_pl']),
        'percent_self_closed': percent_self_closed,
        'n_opened': np.sum(df['n_opened']),
        'percent_closed': percent_closed,
        'total_margin_taken': np.sum(df['n_liquidated'] * df['avg_liquidation_size']),
        'gas_tank_realized_pl': gas_tank_realized_pl,
        'liquidator_md_time_ratio': liquidator_md_time / (liquidator_md_time + gas_tank_md_time),  # risk measure
        'percent_pl_to_liquidator': percent_pl_to_liquidator,
    }