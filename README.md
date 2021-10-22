## Superfluid Liquidations Simulations

This repo includes simulation code to estimate the risk created by Superfluid.finance stream liquidations 
on Ethereum mainnet.

The liquidation system parameters can have nonlinear effects on the system stability and overall cost to the user. 
Because of this system's complexity, these effects are best understood via simulation.

`Simulation_functions.py` encodes the core logic and incentives behind the Superfluid system. In `sim_analysis.py`, we 
use this general framework to explore a simplified liquidations model with a single liquidator and gas tank for USDC 
streams. 

This model provides a baseline performance benchmark for future design iterations. Under this 
naive system, the expected user-incurred cost is around 0.01 ETH per stream. This is high and the simulation results 
show how it can be significantly reduced by modifying several aspects of the design.

The next design iteration will introduce some complexity with a market driven mechanism for setting
minimum margin requirements and an auction-based partial monopoly for liquidators. This simulation framework will 
help us quantify the improvements made by different design decisions and parameter sets. This iteration is 
not included in this repo.

Analysis considers minute median gas price data for March-September 2021. While this does not take into account the 
likely rise in gas price, parameter sets which do not perform well under historical gas data will likely not work 
on future data.

Assumed parameter distributions are in `simulation_parameters.py`.