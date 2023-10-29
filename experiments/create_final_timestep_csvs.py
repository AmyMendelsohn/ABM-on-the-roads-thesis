from experiments.imports import *
###################################################
#########
### CREATE CSVs
#########
###################################################   

def create_location_final_timestep_csv(csv_results_path, subfolder, filename, averaging=False):
    '''Takes a csv file, which has information for every agent at every timestep.
    Creates a new csv file with only the final timestep information for LOCATIONs.
    Writes the new csvs to the outputs/final_step/csv folder.
    Optionally (if averaging=True), averages the values for each location.
    '''
    path = f'{csv_results_path}/{subfolder}/{filename}'
    if subfolder == '':
        path = f'{csv_results_path}/{filename}'
    df = pd.read_csv(path)
    final_timestep_df = df[df['Step'] == df['Step'].max()]
    locations_df = final_timestep_df[final_timestep_df['agent_category']=='location'].copy()
    
    if averaging:
        locations_df = locations_df.groupby(['modern_name']).mean()
        filename = 'AVG_' + filename
    
    save_path = f'outputs/final_step/csvs/{subfolder}'
    if not os.path.exists(save_path):
        os.makedirs(save_path)    
    locations_df.to_csv(f'{save_path}/{filename}')

def create_final_csvs_for_folder(folder_path, overwrite=True):
    '''Calls the create_location_final_timestep_csv function for every file in folder. 
       Gets csvs from the outputs/csv_results folder.
       >>> create_final_csvs_for_folder('outputs/csv_results/dist_mult')
    '''
    subfolder = folder_path.split('outputs/csv_results/')[-1]
    for filename in os.listdir(folder_path):
        should_make = True
        if overwrite is False:
            save_path = f'outputs/final_step/csvs/{subfolder}/'
            if not os.path.exists(save_path):
                os.makedirs(save_path) 
            should_make = filename not in os.listdir(save_path)
        if filename.endswith('.csv') and should_make:
            # with multi-level subpath, need to just take the whole thing after the 'outputs/csv_results'
            create_location_final_timestep_csv('outputs/csv_results', subfolder, filename)


##############
## HELPERS

def get_total_product_at_final_timestep(csv, prod_type):
    '''Given a final_step csv file, return the total amount of product in the system (ie across all locations)
    for the given product type '''
    df = pd.read_csv(csv)
    return df[prod_type].sum()

if __name__ == "__main__":        
    # create_location_final_timestep_csv('outputs/csv_results', 'dist_mult','itineraries_ba_node degree_50_0_(1, 0, 0)_20_400' )
    # path = 'outputs/csv_results/decision_strats/'
    # for folder in os.listdir(path):
    #     if folder != '.DS_Store' and folder in ['itin_ba_1', 'itin_ws_1', 'orbis_ba_1', 'orbis_ws_1']:
    #         create_final_csvs_for_folder(path + folder)
    # create_final_csvs_for_folder('outputs/csv_results/decision_strats/')
    create_final_csvs_for_folder('outputs/csv_results/dist_mult/')
    
