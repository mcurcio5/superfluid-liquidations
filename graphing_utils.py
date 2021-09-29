import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def graph_pl(df, title = 'Simulation Run Highlights'):
    """ graph to verify results, not efficient or pretty """
    fig, axs = plt.subplots(3, 2, figsize=(14, 8))
    colors = sns.color_palette('bright')
    for i, ax in enumerate(axs.flat):
        if i == 0:
            ax.plot(df['liquidator_pl'].cumsum(), color=colors[0])
            ax.set_title('Liquidator Profit & Loss (USD)', fontsize=13)
        elif i == 1:
            ax.plot(df['gas_tank_eth_pl'].cumsum(), color=colors[0])
            ax.set_title('Gas Tank Profit & Loss (ETH)', fontsize=13)
        elif i == 2:
            ax.plot(df['price'], color=colors[1])
            ax.set_title('Price of Ether', fontsize=13)
        elif i == 3:
            ax.plot(df['three_min_median'], color=colors[1])
            ax.set_title('3-Minute Median Gas Price', fontsize=13)
        elif i == 4:
            ax.plot((df['n_opened'].cumsum() - df['n_self_closed'].cumsum() - df['n_liquidated'].cumsum()),
                    color=colors[2])
            ax.set_title('Number of Open Streams', fontsize=13)
        elif i == 5:
            ax.plot(df['n_liquidated'].cumsum(), color=colors[2])
            ax.set_title('Number of Liquidations & Self Closed Streams', fontsize=13)
            ax.plot(df['n_self_closed'].cumsum(), color=colors[3])
            ax.legend(loc='upper left', labels=['Liquidations', 'Self-Closed'], fontsize=12)
        ax.set_xticks([])
        sns.despine(left=True, bottom=True)

    fig.suptitle(title, fontsize=16)
    plt.tight_layout()