# ABM on the Roads

This code accompanies the "ABM on the Roads of Roman Britain", a Master of Computer Science thesis for the University of Melbourne, completed in October 2023.

## How to Run
The model was run with:
- Python 3.9
- Python Mesa 3.1.1
- networkx 2.8.8

Analysis was run with the following python packages:
- matplotlib 3.6.2
- pandas 1.5.2
- seaborn 0.12.1
- statsmodels 0.14.0

To run, clone the repository and run `run_model.py`. You can either open the file in interactive mode and run your command of choice, or uncomment one of the lines provided at the end of the file. 

Results will be saved in a new directory called `outputs`, created in the `experiments` directory.

## Project Structure
This project has 5 folders:
1. `ABM` - model code
2. `experiments` - analysis of model runs
3. `itineraries` - itineraries generation and data files
4. `orbis` - orbis generation and data files
5. `stamps` - code related to CEIPAC stamp data

After running the model at least once, there will be two additional folders created - `outputs` and `social_networks`. `outputs` contains all results, and `social_networks` contains the social network data for each spatial network + number of merchant combination.

## Sources
- ORBIS source files (orbis_routes_topo_o.json, orbis_sites_extended.csv) are from https://github.com/emeeks/orbis_v2
- Stamp data (CEIPAC) is from https://github.com/xrubio/ecologyStamps


