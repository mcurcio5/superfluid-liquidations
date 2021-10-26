## Superfluid Liquidations Simulations

This repo includes simulation code to estimate the risk created by Superfluid.finance stream liquidations 
on Ethereum Mainnet.

The liquidation system parameters can have nonlinear effects on the system stability and overall cost to the user. 
Because of this system's complexity, these effects are best understood via simulation.

`simulation_functions.py` encodes the core logic and incentives behind the Superfluid system. In `sim_analysis.py`, we 
use this general framework to explore a simplified liquidations model with a single liquidator and gas tank for USDC 
streams. 

This model provides a baseline performance benchmark for future design iterations. Under this 
naive system, the expected user-incurred cost is around 0.01 ETH per stream. This is high and the simulation results 
show how it can be significantly reduced by modifying several aspects of the design.

The next design iteration will introduce some complexity with a market driven mechanism for setting
minimum margin requirements and an auction-based partial monopoly for liquidators. This simulation framework will 
help us quantify the improvements made by different design decisions and parameter sets. This iteration is 
not included in this repo.

The graphs in the analysis notebook use minute median gas price data for March-September 2021. While this does not take 
into account the likely future rise in gas price, parameter sets which do not perform well under historical gas data 
will likely not work on future data. 

Thus, we identify poor parameter sets and design choices with high confidence without having to launch a version 
to Mainnet. Additionally, this approach arguably outperforms iteration after launch because it examines thousands of 
unknown parameter combinations, each representing a different user behavior and protocol growth scenario. 

We use this biased expectation of protocol success to estimate what will happen most often and on average given our 
a priori knowledge of the users and system. While success at launch only depends on what user 
behavior and growth actually occurred, estimating an expectation significantly lowers user cost and increases
profitability in the long term.

Assumed parameter distributions are in `simulation_parameters.py`.