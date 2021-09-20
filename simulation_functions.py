#########
# These functions simulate the P&L for the Superfluid liquidations protocol given parameters and data
#########

import pandas as pd
import numpy as np
from numpy.random import default_rng

pd.options.mode.chained_assignment = None
rng = default_rng()

####
# constants
####

LIQUIDATION_GAS_USED = 300000
GAMMA_K = 4  # param for stream size distribution


####
# conversion functions
####

def gwei_to_eth(g):
    return g * 10 ** -9


def month_to_hour(x):
    return x / 30 / 24


def month_to_minute(x):
    return x / 30 / 24 / 60


def minute_to_month(x):
    return x / 60 / 24 / 30


def percent_to_dec(x):
    return x / 100


def stream_rate_to_margin(stream_rate, margin_hours):
    return month_to_hour(stream_rate) * margin_hours


####
# stream & liquidation arrival time simulation functions
####

def sample_new_stream_times(n_minutes, params):
    """ evenly distributes new stream opening times via uniform distribution over full time interval
        assumes constant arrival of new streams """
    n_months = minute_to_month(n_minutes)
    expected_stream_openings = int(params['monthly_opened_streams'] * n_months // 1)
    return rng.uniform(0, n_minutes, expected_stream_openings).astype(int)


def calculate_liquidation_probabilities(params):
    """ calculates probabilities of self-closed vs liquidation events from params """
    prob_self_closed = 1 / (params['average_stream_lifetime'] * 24 * 60)
    prob_liquidated = percent_to_dec(month_to_minute(params['percent_accidently_liquidated_per_month']))
    prob_closing_tx_is_liquidation = prob_liquidated / (prob_liquidated + prob_self_closed)

    return prob_self_closed, prob_liquidated, prob_closing_tx_is_liquidation


def remove_invalid_times(times, n_minutes):
    """ gets rid of events that occur after the current time window """
    return times[np.asarray(times < n_minutes)].astype(int)


def simulate_naive_liquidation_times(times, n_minutes, params):
    """ simulates arrival of self-closes and liquidations without considering incentives """
    n_samples = times.shape[0]
    prob_self_closed, prob_liquidated, prob_closing_tx_is_liquidation = calculate_liquidation_probabilities(params)

    times = times + np.minimum(rng.exponential(1 / prob_liquidated, n_samples),
                               rng.exponential(1 / prob_self_closed, n_samples))
    liquidation_mask = np.asarray(rng.uniform(0, 1, n_samples) < prob_closing_tx_is_liquidation)

    liquidation_times = times[liquidation_mask]
    self_closed_times = times[~liquidation_mask]

    return remove_invalid_times(liquidation_times, n_minutes), remove_invalid_times(self_closed_times, n_minutes)


def sample_stream_sizes(liquidations_size, self_closed_size, params):
    """ samples stream sizes from gamma distribution """
    theta = params['average_stream_size'] / (2 * np.sqrt(GAMMA_K))
    return rng.gamma(GAMMA_K, theta, size=liquidations_size), rng.gamma(GAMMA_K, theta, size=self_closed_size)


def get_deliberate_liquidations(gas_price, eth_price, self_closed_times, self_closed_sizes, params):
    """ returns mask of self-closed liquidations where user opts to deliberately default due to high gas costs """
    self_closing_cost = gwei_to_eth(gas_price[self_closed_times]) * LIQUIDATION_GAS_USED * eth_price[
        self_closed_times] + params['min_self_liquidation_savings']
    self_closing_margin_value = stream_rate_to_margin(self_closed_sizes, params['upfront_hours'])
    return np.asarray(self_closing_cost > self_closing_margin_value)


def filter_liquidations_by_size(liquidation_times, self_closed_times, gas_price, eth_price, n_minutes, params):
    """ considers that if self-closing cost + min_liquidation_savings > margin value, liquidate at 100% frequency
        smaller streams, thus, get liquidated at a high frequency """
    liquidation_sizes, self_closed_sizes = sample_stream_sizes(liquidation_times.shape[0],
                                                               self_closed_times.shape[0], params)

    deliberate_liquidations_mask = get_deliberate_liquidations(gas_price, eth_price, self_closed_times,
                                                               self_closed_sizes, params)

    liquidation_times = np.concatenate([liquidation_times, self_closed_times[deliberate_liquidations_mask]])
    liquidation_sizes = np.concatenate([liquidation_sizes, self_closed_sizes[deliberate_liquidations_mask]])

    self_closed_times = self_closed_times[~deliberate_liquidations_mask]
    self_closed_sizes = self_closed_sizes[~deliberate_liquidations_mask]

    return liquidation_times, self_closed_times, liquidation_sizes, self_closed_sizes


def simulate_stream_ends(times, gas_price, eth_price, n_minutes, params):
    """ simulate stream closing times, types, and sizes """
    liquidation_times, self_closed_times = simulate_naive_liquidation_times(times, n_minutes, params)
    return filter_liquidations_by_size(liquidation_times, self_closed_times, gas_price, eth_price, n_minutes, params)


def simulate_streams(df, params):
    """ simulates stream start & end times, stream sizes, self-closings, liquidations """
    n_minutes = df.shape[0]
    new_stream_times = sample_new_stream_times(n_minutes, params)
    liquidation_times, self_closed_times, liquidation_sizes, self_closed_sizes = simulate_stream_ends(
        new_stream_times, np.array(df['median_gas_price']), np.array(df['price']), n_minutes, params)

    return new_stream_times, liquidation_times, self_closed_times, liquidation_sizes, self_closed_sizes


def bin_times_and_sizes(times, n_minutes, sizes=False):
    """ bins the arrivals and avg liquidation sizes into 1 min intervals """
    unique_values, indices, counts = np.unique(times, return_index=True, return_counts=True)

    binned_times = np.zeros(n_minutes)
    binned_times[unique_values] = counts

    if type(sizes) == np.ndarray:
        binned_sizes = np.zeros(n_minutes)
        binned_sizes[unique_values] = sizes[indices]  # doesn't average sizes if multiple arrivals, but efficient

        return binned_times, binned_sizes

    return binned_times


def run_simulations_and_include_in_df(df, params):
    """ runs simulations and appends results to df """
    n_minutes = df.shape[0]
    new_stream_times, liquidation_times, self_closed_times, liquidation_sizes, self_closed_sizes = simulate_streams(df, params)

    df['n_opened'] = bin_times_and_sizes(new_stream_times, n_minutes, sizes=False)
    liquidation_binned_times, liquidation_binned_sizes = bin_times_and_sizes(liquidation_times, n_minutes,
                                                                             sizes=liquidation_sizes)
    self_closed_binned_times, self_closed_binned_sizes = bin_times_and_sizes(self_closed_times, n_minutes,
                                                                             sizes=self_closed_sizes)

    df['n_liquidated'] = liquidation_binned_times
    df['n_self_closed'] = self_closed_binned_times
    df['avg_liquidation_size'] = liquidation_binned_sizes
    df['avg_self_closed_size'] = self_closed_binned_sizes

    return df


def calculate_liquidator_pl(df, params):
    """ calculates liquidator's profit & loss for each minute """
    return (df['n_liquidated'] * stream_rate_to_margin(df['avg_liquidation_size'], params['upfront_hours']) -
            LIQUIDATION_GAS_USED * df['n_liquidated'] * gwei_to_eth(df['median_gas_price']) * df['price'] * (
                    1 - params['refund_rate']))


def calculate_all_pl(df, params):
    """ calculate profit & loss for liquidator and gas tank """
    df['liquidator_pl'] = calculate_liquidator_pl(df, params)

    df['gas_refunded_eth'] = LIQUIDATION_GAS_USED * df['n_liquidated'] * gwei_to_eth(df['median_gas_price']) * params[
        'refund_rate']
    df['gas_tank_eth_pl'] = df['n_opened'] * params['upfront_fee'] - df['gas_refunded_eth']
    df['gas_tank_usd_pl'] = df['gas_tank_eth_pl'] * df['price']

    return df


def simulate_and_calculate_pl(df, params):
    """ simulates liquidations data and calculates profit & loss over data provided in df """
    df = run_simulations_and_include_in_df(df, params)
    return calculate_all_pl(df, params)
