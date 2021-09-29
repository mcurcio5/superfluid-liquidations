import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def graph_pl(df):
    """ graph to verify results, not efficient or pretty """
    fig, axs = plt.subplots(3, 2, figsize=(12, 8))
    for i, ax in enumerate(axs.flat):
        if i == 0:
            df['liquidator_pl'].cumsum().plot(ax=ax)
            ax.set_title('Liquidator Profit & Loss (USD)', fontsize=13)
        elif i == 1:
            df['gas_tank_eth_pl'].cumsum().plot(ax=ax)
            ax.set_title('Gas Tank Profit & Loss (ETH)', fontsize=13)
        elif i == 2:
            df['price'].plot(ax=ax)
            ax.set_title('Price of Ether', fontsize=13)
        elif i == 3:
            df['three_min_median'].plot(ax=ax)
            ax.set_title('3-Minute Median Gas Price', fontsize=13)
        elif i == 4:
            (df['n_opened'].cumsum() - df['n_self_closed'].cumsum() - df['n_liquidated'].cumsum()).plot(ax=ax)
            ax.set_title('Number of Open Streams', fontsize=13)
        elif i == 5:
            df['n_liquidated'].cumsum().plot(ax=ax)
            ax.set_title('Number of Liquidations & Self Closed Streams', fontsize=13)
            df['n_self_closed'].cumsum().plot(ax=ax)
            ax.legend(loc='upper left', labels=['Liquidations', 'Self-Closed'], fontsize=12)
        ax.set_xticks([])
        sns.despine(left=True, bottom=True)

    fig.suptitle('Simulation Run Highlights', fontsize=16)
    plt.tight_layout()