#########
# These functions simulate the profit & loss for Superfluid liquidations given parameters and data
#########

import pandas as pd
import numpy as np
from numpy.random import default_rng

from simulation_parameters import sample_params
from metrics_extraction import calculate_metrics

pd.options.mode.chained_assignment = None
rng = default_rng()

####
# constants
####

OPEN_GAS = 228000
LIQUIDATION_GAS = 223000
STANDARD_TX_GAS = 140000


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
    """ calculates probabilities of self-closed vs liquidation events """
    prob_self_closed = 1 / (params['average_stream_lifetime'] * 24 * 60)
    prob_liquidated = percent_to_dec(month_to_minute(params['percent_accidently_liquidated_per_month']))
    prob_closing_tx_is_liquidation = prob_liquidated / (prob_liquidated + prob_self_closed)

    return prob_self_closed, prob_liquidated, prob_closing_tx_is_liquidation


def remove_invalid_times(times, sizes, n_minutes):
    """ removes events that occur after the time window """
    mask = np.asarray(times < n_minutes)

    return times[mask].astype(int), sizes[mask]


def simulate_naive_liquidation_times(times, sizes, n_minutes, params):
    """ simulates arrival of self-closes and liquidations without considering user's incentives """
    n_samples = times.shape[0]
    prob_self_closed, prob_liquidated, prob_closing_tx_is_liquidation = calculate_liquidation_probabilities(params)

    times = times + np.minimum(rng.exponential(1 / prob_liquidated, n_samples),
                               rng.exponential(1 / prob_self_closed, n_samples))
    liquidation_mask = np.asarray(rng.uniform(0, 1, n_samples) < prob_closing_tx_is_liquidation)

    liquidation_times = times[liquidation_mask]
    liquidation_sizes = sizes[liquidation_mask]
    liquidation_times, liquidation_sizes = remove_invalid_times(liquidation_times, liquidation_sizes, n_minutes)

    self_closed_times = times[~liquidation_mask]
    self_closed_sizes = sizes[~liquidation_mask]
    self_closed_times, self_closed_sizes = remove_invalid_times(self_closed_times, self_closed_sizes, n_minutes)

    return liquidation_times, liquidation_sizes, self_closed_times, self_closed_sizes


def identify_deliberate_liquidations(gas_price, eth_price, self_closed_times, self_closed_sizes, params):
    """ returns mask of self-closed liquidations where user opts to deliberately default due to high gas costs
        note: user can always transfer money out of wallet for cost of STANDARD_TX_GAS """
    self_closing_cost = gwei_to_eth(gas_price[self_closed_times]) * (LIQUIDATION_GAS - STANDARD_TX_GAS) * eth_price[
        self_closed_times] - params['min_self_liquidation_savings']
    self_closing_margin_value = stream_rate_to_margin(self_closed_sizes, params['upfront_hours'])

    return np.asarray(self_closing_cost > self_closing_margin_value)


def convert_small_self_closes_to_liquidations(liquidation_times, liquidation_sizes, self_closed_times,
                                              self_closed_sizes, gas_price, eth_price, params):
    """ liquidates at 100% frequency where self-closing cost - min_self_liquidation_savings - standard tx cost > margin
        liquidates small streams at a high frequency """
    deliberate_liquidations_mask = identify_deliberate_liquidations(gas_price, eth_price, self_closed_times,
                                                                    self_closed_sizes, params)

    liquidation_times = np.concatenate([liquidation_times, self_closed_times[deliberate_liquidations_mask]])
    liquidation_sizes = np.concatenate([liquidation_sizes, self_closed_sizes[deliberate_liquidations_mask]])

    self_closed_times = self_closed_times[~deliberate_liquidations_mask]
    self_closed_sizes = self_closed_sizes[~deliberate_liquidations_mask]

    return liquidation_times, self_closed_times, liquidation_sizes, self_closed_sizes


def simulate_stream_ends(times, sizes, gas_price, eth_price, n_minutes, params):
    """ simulate stream closing times and sizes for self-closed and liquidations """
    liquidation_times, liquidation_sizes, self_closed_times, self_closed_sizes = simulate_naive_liquidation_times(
        times, sizes, n_minutes, params)

    return convert_small_self_closes_to_liquidations(liquidation_times, liquidation_sizes, self_closed_times,
                                                     self_closed_sizes, gas_price, eth_price, params)


def sample_stream_sizes(stream_times, stream_gas_prices, stream_eth_prices, params):
    """ samples stream sizes from gamma distribution and removes those where tx cost > month stream value
        assumes constant stream size distribution over time, so during less streams will be opened on average """
    gamma_k = params['distribution_inverse_skewness']
    theta = params['average_stream_size'] / gamma_k  # based on assumed distribution
    stream_costs = ((OPEN_GAS * gwei_to_eth(stream_gas_prices) + params['upfront_fee']) *  # upfront fee + gas cost
                    stream_eth_prices * params['lowest_stream_cost_ratio'])  # do we want to add margin here too?

    stream_sizes = rng.gamma(gamma_k, theta, size=stream_times.shape[0])
    opened_streams_mask = np.asarray(stream_sizes > stream_costs)  # streams smaller than current cost not opened

    return stream_times[opened_streams_mask], stream_sizes[opened_streams_mask]


def simulate_streams(df, params):
    """ simulates stream start and end times, stream sizes, self-closings, liquidations """
    n_minutes = df.shape[0]
    new_stream_times = sample_new_stream_times(n_minutes, params)
    # simulate stream sizes
    new_stream_gas_prices = np.array(df['median_gas_price'])[new_stream_times]
    new_stream_eth_prices = np.array(df['price'])[new_stream_times]
    new_stream_times, new_stream_sizes = sample_stream_sizes(new_stream_times, new_stream_gas_prices,
                                                             new_stream_eth_prices, params)

    liquidation_times, self_closed_times, liquidation_sizes, self_closed_sizes = simulate_stream_ends(
        new_stream_times, new_stream_sizes, np.array(df['median_gas_price']), np.array(df['price']), n_minutes, params)

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


def simulate_streams_and_liquidations(df, params):
    """ simulates streams and liquidations data """
    n_minutes = df.shape[0]
    new_stream_times, liquidation_times, self_closed_times, liquidation_sizes, self_closed_sizes = simulate_streams(df,
                                                                                                                    params)

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


####
# functions for calculating a simulation run's profit & loss for gas tank and liquidator
####


def calculate_liquidator_pl(df, params):
    """ calculates liquidator's profit & loss given no gas prediction capability """
    return (df['n_liquidated'] * stream_rate_to_margin(df['avg_liquidation_size'], params['upfront_hours']) -
            LIQUIDATION_GAS * df['n_liquidated'] * gwei_to_eth(df['median_gas_price']) * df['price'] * (
                    1 - params['refund_rate']))


def calculate_liquidator_pl_with_prediction(df, params):
    """ calculates the profit & loss for a liquidator that can perfectly predict gas price n minutes ahead
        function assumes that they cannot predict ETH prices """
    n = int(params['gas_prediction_ability'] * 60)  # n minutes
    gas_prices = np.array(df['three_min_median'])  # use 3 min median gas price for accurate execution prices
    output_n_rows = gas_prices.shape[0] - n + 3

    l_mask = np.asarray(np.array(df['n_liquidated']) > 0)  # for selecting rows in full df
    l_mask_subset = l_mask[:output_n_rows]  # excludes rows at end of dataset without full window of data

    # gas indices create windows of size n - 2 by referencing indices in gas_prices
    gas_indices = np.arange(n - 2)[None, :] + np.arange(output_n_rows)[l_mask_subset][:, None]
    n_rows = gas_indices.shape[0]  # n rows in subspace of only rows with liquidations

    posted_margin = stream_rate_to_margin(np.array(df['avg_liquidation_size'])[:output_n_rows][l_mask_subset], params['upfront_hours'])
    stream_per_minute = month_to_minute(np.array(df['avg_liquidation_size'])[:output_n_rows][l_mask_subset])
    eth_price = np.array(df['price'])[:output_n_rows][l_mask_subset]

    remaining_margin = posted_margin[:, None] - np.arange(n - 2)[None, :] * stream_per_minute[:, None]
    tx_costs = LIQUIDATION_GAS * gwei_to_eth(gas_prices[gas_indices]) * eth_price[:n_rows, None] * (
            1 - params['refund_rate'])  # for every possible time per liquidation

    liquidator_profits = remaining_margin - tx_costs
    best_execution_indices = np.argmax(liquidator_profits, axis=1)

    df = df[:output_n_rows]  # cuts end of df due to window size

    gas_prices_paid = np.zeros(output_n_rows)  # initialize for speed
    liquidator_pl = np.zeros(output_n_rows)

    gas_prices_paid[l_mask_subset] = gas_prices[gas_indices][np.arange(n_rows), best_execution_indices]
    liquidator_pl[l_mask_subset] = liquidator_profits[np.arange(n_rows), best_execution_indices]

    df['gas_price_paid'] = gas_prices_paid
    df['liquidator_pl'] = liquidator_pl

    return df


def calculate_gas_tank_pl(df, params):
    """ calculates gas tank profit & loss in eth and usd """
    eth_price_col = 'median_gas_price' if params['gas_prediction_ability'] <= 3 / 60 else 'gas_price_paid'

    df['gas_refunded_eth'] = LIQUIDATION_GAS * df['n_liquidated'] * gwei_to_eth(df[eth_price_col]) * params['refund_rate']
    df['gas_tank_eth_pl'] = df['n_opened'] * params['upfront_fee'] - df['gas_refunded_eth']
    df['gas_tank_usd_pl'] = df['gas_tank_eth_pl'] * df['price']

    return df


def calculate_pl(df, params):
    """ calculate profit & loss for liquidator and gas tank """
    if params['gas_prediction_ability'] <= 3 / 60:  # minimum is 3 minutes for function to work
        df['liquidator_pl'] = calculate_liquidator_pl(df, params)
    else:
        df = calculate_liquidator_pl_with_prediction(df, params)

    return calculate_gas_tank_pl(df, params)


####
# aggregate function
####


def simulate_and_calculate_pl(df, params, deep_copy=False):
    """ simulates liquidations data and calculates profit & loss over provided gas and eth price data """
    if deep_copy:  # one line if else is significantly slower
        df = df.copy(deep=True)

    df = simulate_streams_and_liquidations(df, params)

    return calculate_pl(df, params)


def simulate_and_calculate_n_times(df, n_sims=1000):
    """ simulates and calculates metrics for simulations """
    output = np.zeros((n_sims, 20))
    for i in range(n_sims):
        local_df = df.copy(deep=True)
        params = sample_params()
        local_df = simulate_and_calculate_pl(local_df, params)
        metrics = calculate_metrics(local_df, params)
        metrics_dict = {**params, **metrics}
        output[i, :] = list(metrics_dict.values())

    return pd.DataFrame(data=output, columns=list(metrics_dict.keys()))
