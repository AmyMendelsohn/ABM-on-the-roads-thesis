import sys, os
sys.path.append("..")
from create_final_timestep_csvs import create_final_csvs_for_folder
from run_final_timestep_charts import run_all_charts_for_folder
from run_anova import combine_anova_files, create_anova_files_for_folder, make_four_interaction_plots
from figures_anova_boxplot import call_for_all_networks, call_for_all_num_merchants, create_boxplot_product_by_decision_strats, create_boxplot_product_by_dist, create_boxplot_product_by_num_merchants, boxplot_prod_by_type_and_distmult, create_four_heatmaps
from experiments.helper_functions import pretty_name

######
# Helper script to make report content.
######
NETWORKS = ['itin_ba', 'itin_ws', 'orbis_ba', 'orbis_ws']
NUM_MERCHANTS = [50, 200, 400]
EXPERIMENTS = ['dist_mult', 'decision_strats']


def final_csvs(main_folder_name, overwrite=True):
    '''Create final csvs'''
    path = f'outputs/csv_results/{main_folder_name}'
    for folder in os.listdir(path):
        if folder !='.DS_Store':
            create_final_csvs_for_folder(f'{path}/{folder}', overwrite=overwrite)

    print("finished making final csvs")

# Run Anova
def anova_create(main_folder_name, final_step_path):
    create_anova_files_for_folder(final_step_path)
    combine_anova_files(main_folder_name)

def anova_stats(main_folder_name, all_anova_file):
    if main_folder_name == 'decision_strats':
        folder_name = 'decision_strat'
    else:
        folder_name = main_folder_name
    make_four_interaction_plots(all_anova_file, expr_var=folder_name)
    

########## Create boxplots
def boxplots(main_folder_name, all_anova_file):
    if 'dist' in main_folder_name:
        for n in [50, 200, 400]:
            call_for_all_networks(func=boxplot_prod_by_type_and_distmult, 
                            num_merchants=n,
                            all_anova_file=all_anova_file, 
                            expr_var=main_folder_name)
        call_for_all_num_merchants(func=create_boxplot_product_by_dist, 
                                   all_anova_file=all_anova_file, 
                                   expr_var=main_folder_name)
    else:
        call_for_all_num_merchants(
            create_boxplot_product_by_decision_strats,
            all_anova_file=all_anova_file,
            expr_var=main_folder_name)

    call_for_all_networks(func=create_boxplot_product_by_num_merchants, 
                          all_anova_file=all_anova_file, 
                          just_network=True,
                          expr_var=main_folder_name)

######### Create heatmaps
def heatmaps(main_folder_name, final_step_path):
    if main_folder_name == 'decision_strats':
        folder_name = 'decision_strat'
    else:
        folder_name = main_folder_name
    label = pretty_name(folder_name)
    for agg_type in ['mean', 'var', 'median']:
        create_four_heatmaps(path=final_step_path, 
                                x_var=folder_name,
                                x_label=label,
                                agg_type=agg_type)
    
#### Running everything
def make_all_report_content():
    '''Run this function to generate EVERYTHING, assuming that the initial csvs have been created.'''
    for main_folder_name in EXPERIMENTS:
        final_step_path = f'outputs/final_step/csvs/{main_folder_name}/'
        all_anova_file = f'outputs/final_step/csvs/{main_folder_name}/anova_all_networks.csv'
        final_csvs(main_folder_name, overwrite=False)
        
        run_all_charts_for_folder(main_folder_name) #overwrite=False by default
    
        anova_create(main_folder_name, final_step_path)
        anova_stats(main_folder_name, all_anova_file)
        ## boxplots and heatmaps need Anova Stats to run at least once first!
        boxplots(main_folder_name, all_anova_file)
        heatmaps(main_folder_name, final_step_path)

if __name__ == '__main__':
    make_all_report_content()