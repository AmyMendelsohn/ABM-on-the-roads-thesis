import sys, time, os
sys.path.append("..")
from ABM.constants import *
from ABM.model import MerchantModel, mesa
import pandas as pd
import time, os
from experiments.helper_functions import convert_to_folder_name

# This file is to automate running experiments over multiple param combinations,
# and produce whatever graphs are specified in `run_experiments.py` for each.

ITERATIONS = 30   
spatial_networks = [
                    ITINERARIES, 
                    ORBIS
                    ]
social_networks = [BA_GRAPH, 
                   WATTS_GRAPH,
                   ]
merchant_numbers = [50, 200, 400]
distance_multipliers = [0, 0.1, 0.5, 0.8, 1]
DECISION_STRATS = [(1,0,0), 
                   (0,1,0), 
                   (0,0,1), 
                   (0.3,0.3,0.4), 
                   (0.5, 0.5, 0), 
                   (0, 0.5, 0.5), 
                   (0.5, 0, 0.5)]
specialist_decision_strats = [(0,0,1), 
                            (0.3,0.3,0.4),
                            (0, 0.5, 0.5), 
                            (0.5, 0, 0.5)]

def do_model_runs(spatial, 
                  social, 
                  num_merchants, 
                  prod_criteria,
                  distance_mult,
                  proportions,
                  id_num, num_iterations, max_steps=100, 
                  save_folder_start='experiments/outputs/csv_results/',
                  replacing=False):
    '''Do `num_iterations` runs of the model with these parameters. 
    - id_num is used to create the filename for the final png.
    - `save_folder_start` is something like 'outputs/csv_results/dist_mult/', 
    ie the full folder path that will contain a new folder (if not already 
    existing) with spatial_social, ie itin_ba
    '''
    
    title = f"{spatial}, {social}, merchants: {num_merchants}, dist_mult: {distance_mult}, proportions: {proportions} \n \
              num iterations: {num_iterations}"
    
    profit, generalist, specialist = proportions
    params = {  "num_merchants":        num_merchants,
                "num_locations":        get_num_locations(spatial),
                "spatial_network_type": spatial,
                "social_network_type" : social,
                "producer_criteria"   : prod_criteria,
                "distance_multiplier":  distance_mult,
                "discard_fraction":     0.14,
                "proportion_profit":    profit,
                "proportion_generalist": generalist,
                "proportion_specialist": specialist,
                "no_trade_tolerance":  -1,
                "location_trades": False
    }
    
    output_folder = f'{save_folder_start}/{convert_to_folder_name(spatial, social)}'
    csv_results_filename = f'{spatial}_{social}_{prod_criteria}_{num_merchants}_{distance_mult}_{proportions}_{num_iterations}_{max_steps}'
    file_path = f'{output_folder}/{csv_results_filename}.csv'
    
    if replacing==False and os.path.exists(file_path):
        print("FILE FOUND, not replacing: ", csv_results_filename)
        return

    results = mesa.batch_run(
        MerchantModel,
        parameters=params,
        iterations=num_iterations,
        max_steps=max_steps,
        number_processes=1,
        data_collection_period=1,
        display_progress=True
    )
    
    df = pd.DataFrame(results)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    df.to_csv(file_path)
    
    return csv_results_filename

def test_decision_strat(social_net, mer, dist_mult, 
                        spatial_networks=spatial_networks, 
                        specialist=False):
    '''For each decision strat (7),
        On the GIVEN social network with the GIVEN number of merchants and dist_mult,
        Generate a pair of graphs for each spatial network'''
    if specialist:
        strats = specialist_decision_strats
    else:
        strats = DECISION_STRATS
    for dec_strat in strats:
        id_num = 0
        for spatial in spatial_networks:
            do_model_runs(spatial=spatial, 
                                social=social_net, 
                                num_merchants=mer,
                                prod_criteria=NODE_DEGREE,
                                distance_mult = dist_mult, 
                                proportions=dec_strat,
                                id_num=id_num,
                                num_iterations=30, 
                                max_steps=400, 
                                save_folder_start=f'experiments/outputs/csv_results/decision_strats/')
            id_num += 1
            
def test_decision_varying_merchants(social_net, 
                                    dist_mult, 
                                    spatial_networks=spatial_networks, 
                                    specialist=False):
    for mer in merchant_numbers:
        test_decision_strat(social_net, 
                            mer, 
                            dist_mult, 
                            spatial_networks=spatial_networks, 
                            specialist=specialist)
        
def test_decision_varying_social():
    for social in social_networks:
        test_decision_varying_merchants(social, dist_mult=0.5)

def test_dist_mult(social_net, spatial_networks=spatial_networks):
    '''For each spatial network,
        On the GIVEN social network,
        Generate 5 pairs of graphs (one for each distance multiplier) for each merchant number (5*3 pairs)'''
    for spatial in spatial_networks:
        id_num = 0
        for mer in merchant_numbers:
            for dist_mult in distance_multipliers:
                do_model_runs(spatial=spatial, 
                                    social=social_net, 
                                    num_merchants=mer,
                                    prod_criteria=NODE_DEGREE,
                                    distance_mult = dist_mult, 
                                    proportions=(1,0,0),
                                    id_num=id_num,
                                    num_iterations=30, 
                                    max_steps=400,
                                    save_folder_start=f'experiments/outputs/csv_results/dist_mult/')
                id_num += 1
    
if __name__ == '__main__':
    print("Start Time: ", time.ctime())
    
    ## FOUR THINGS TO RUN
    # test_dist_mult(BA_GRAPH, spatial_networks=[ITINERARIES, ORBIS])
    # test_dist_mult(WATTS_GRAPH, spatial_networks=[ITINERARIES, ORBIS])
    # test_decision_varying_merchants(BA_GRAPH, 1, spatial_networks=[ITINERARIES, ORBIS])
    # test_decision_varying_merchants(WATTS_GRAPH, 1, spatial_networks=[ITINERARIES, ORBIS])
    
    # quickly_run()
        
    



