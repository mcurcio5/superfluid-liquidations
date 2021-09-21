import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def graph_pl(df):
    """ graph to verify results, not efficient or pretty """
    fig, axs = plt.subplots(3, 3, figsize=(18, 14))
    for i, ax in enumerate(axs.flat):
        if i == 0:
            df['liquidator_pl'].cumsum().plot(ax=ax)
            ax.set_title('liquidator p&l')
        elif i == 1:
            df['gas_tank_eth_pl'].cumsum().plot(ax=ax)
            ax.set_title('gas tank eth p&l')
        elif i == 2:
            df['gas_tank_usd_pl'].cumsum().plot(ax=ax)
            ax.set_title('gas tank usd p&l')
        elif i == 3:
            df['price'].plot(ax=ax)
            ax.set_title('price of eth')
        elif i == 4:
            df['avg_median'].plot(ax=ax)
            ax.set_title('avg median gas price')
        elif i == 5:
            (df['n_opened'].cumsum() - df['n_self_closed'].cumsum() - df['n_liquidated'].cumsum()).plot(ax=ax)
            ax.set_title('n streams open')
        elif i == 6:
            df['n_liquidated'].cumsum().plot(ax=ax)
            ax.set_title('n liquidations and self closed (orange)')
            df['n_self_closed'].cumsum().plot(ax=ax)
        elif i == 7:
            df.loc[df['liquidator_pl'] != 0, 'liquidator_pl'].hist(bins=100, ax=ax)
            ax.set_title('liquidation event p&ls')
        elif i == 8:
            df['n_opened'].cumsum().plot(ax=ax)
            ax.set_title('total streams opened')
        ax.set_xticks([])