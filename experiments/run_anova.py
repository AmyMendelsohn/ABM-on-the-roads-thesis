from collections import namedtuple
import sys
sys.path.append("..")
from experiments.create_final_timestep_csvs import get_total_product_at_final_timestep
from ABM.constants import *
import os, pandas as pd
import matplotlib.pyplot as plt, seaborn as sns
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.graphics.factorplots import interaction_plot
from experiments.helper_functions import save_fig, pretty_name

def convert_one_file_to_ANOVA_df(filepath, location, product_type):
    '''Given the filepath to a final_step csv, return a dataframe with the summary
    information for the two variables of interest.
    >>>convert_one_file_to_ANOVA_df(
        f'outputs/final_step/csvs/{csv_results_filename}.csv', 
        'London',
        'PRODUCT_A Product')'''    
    final_timestep_df = pd.read_csv(filepath, encoding='latin-1')
    filename = filepath.split('/')[-1].split('.csv')[0]
    split_name = filename.split('_')
    num_merchants = split_name[3]
    dist_mult = split_name[4]
    decision_strat = split_name[5]
    location_df = final_timestep_df[final_timestep_df['agent_location'] == location].copy()
    total = get_total_product_at_final_timestep(filepath, product_type)
    
    return pd.DataFrame({'num_merchants': num_merchants,
                         'dist_mult': dist_mult,
                         'decision_strat': decision_strat,
                         'product_amount': location_df[product_type],
                         'product_amount_b': location_df['PRODUCT_B Product'],
                         'product_amount_c': location_df['PRODUCT_C Product'],
                         'total_product_in_system': total
                         }).reset_index(drop=True)

def create_two_way_df(folder_path, location, product_type):
    '''Go through each file in the folder, getting the final product
    for the given `product_type` at `location`. Write processed info to file
    and return a dataframe with the information'''
    new_filename = f'{folder_path}/anova_{folder_path.split("/")[-1]}.csv'
    frames = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.csv') and not 'anova' in filename:
            df = convert_one_file_to_ANOVA_df(f'{folder_path}/{filename}', location, product_type)
            frames.append(df)
    result = pd.concat(frames)
    result.to_csv(new_filename)
    return result

def get_df_decision_strategies_of_interest(df, dec_strats=[]):
    '''Starting from a two_way_df, return a df that only contains rows that have the decision strategies
    given in the `dec_strats` list. The list should have each decision strategy as a single string.'''
    return df[df['decision_strat'].isin(dec_strats)].copy()


def do_two_way_anova_test(df, var1, var2, result):
    '''Runs a two way anova using a linear model'''
    model = ols(f'{result} ~ C({var1}) + C({var2}) + C({var1}):C({var2})', data=df).fit()
    print(sm.stats.anova_lm(model, typ=2))
    
def create_anova_files_for_folder(path):
    for folder in os.listdir(path):
        if folder != '.DS_Store' and folder != 'anova_all_networks.csv':
            create_two_way_df(path + folder, 'London', 'PRODUCT_A Product')
    
def anova_over_one_network(filepath= 'outputs/final_step/csvs/dist_mult/itin_ba', 
                           prod_ratios=False,
                           var2='dist_mult'):
    '''Main runner for the ANOVA test, over one specific network (ie IB).
    Sample usage: 
    >>> path = 'outputs/final_step/csvs/dist_mult/'
    >>> create_anova_files_for_folder(path)
    >>> main(filepath=f'{path}/itin_ba', prod_ratios=False, var2='dist_mult')'''
    
    location, prod = 'London', 'PRODUCT_A Product' # CHANGE OTHER PRODUCT PART
    var1, var2, result = 'num_merchants', var2, 'product_ratios'
    print(f"ANOVA two way: \n \
          {filepath.split('/')[-1]} \n \
          location: {location}, prod: {prod}")

    two_way_df = create_two_way_df(filepath, location, prod)

    if prod_ratios:
        # create product ratios
        two_way_df['product_ratios'] = two_way_df['product_amount'] / two_way_df['total_product_in_system']
        two_way_df['product_ratios_b'] = two_way_df['product_amount_b'] / two_way_df['total_product_in_system']
        two_way_df['product_ratios_c'] = two_way_df['product_amount_c'] / two_way_df['total_product_in_system']
        
        result = 'product_ratios'
    
    do_two_way_anova_test(two_way_df, var1, var2, result)
    
def anova_over_all_networks(all_anova_path, var2='dist_mult', value_vars=[], spatial=None):
    '''This does anova over all networks. `value_vars`, if an empty list, means
    that the total sum of all types of product will be used to create the product ratio
    used as the `result`. To only look at one type of product, make a list like 
    `['a']` for product A'''
    for i, val in enumerate(value_vars):
        value_vars[i] = f'product_ratios_{val}'
    var1, result, df = get_melted_anova_df(all_anova_path, var2, value_vars, spatial=spatial)
    print(f'var1: {var1}, var2: {var2}, spatial: {spatial}')
    do_two_way_anova_test(df, var1, var2, result)

def get_melted_anova_df(all_anova_path, var2, value_vars, spatial=None):
    var1, result = 'network', 'product_ratios'
    df = pd.read_csv(all_anova_path) 
    if spatial is not None:
        df = df.loc[(df['network']==f'{spatial}_ba') | (df['network'] == f'{spatial}_ws'), :]
        
    df['product_ratios_a'] = df['product_amount'] / df['total_product_in_system']
    df['product_ratios_b'] = df['product_amount_b'] / df['total_product_in_system']
    df['product_ratios_c'] = df['product_amount_c'] / df['total_product_in_system']
    if value_vars == []:
        value_vars = ['product_ratios_a', 'product_ratios_b','product_ratios_c']
    
    print(f"ANOVA two way: \n \
          {all_anova_path.split('/')[-1]} \n \
          value_vars: {value_vars}")
    
    df = pd.melt(df, id_vars=[var2, var1], 
             value_vars=value_vars,
             var_name='product_type',
             value_name='product_ratios')
   
    return var1, result, df
    
def make_interaction_plot(file, 
                          var2='decision_strat',
                          value_vars=[], 
                          prod_letter='all', 
                          expr_var=''):
    ''' Makes an interaction plot for var2 vs the variables in value_vars.
    If value_vars is an empty list, then it takes the sum of ALL product types.
    The `prod_letter` needs to be set to create the file name.
    >>> make_interaction_plot(anova_all_file, value_vars='product_ratios_c', prod_letter='c')
    '''
    var1, result, df = get_melted_anova_df(file, var2, value_vars)
    colors = sns.color_palette('deep', as_cmap=True)
    # # color list must be exactly the number of trace elems
    if var2 == 'dist_mult': 
        colors = colors[:5] 
    else:
        colors = colors[:7]
    
    x_label, y_label = 'Network', 'Mean of Product Ratios'
    fig_var1, fig_var2 = pretty_name(var1), pretty_name(var2)
    legend_title, fig_title = fig_var2, f"Interaction Plot between {fig_var1} and {fig_var2} for Product {prod_letter.upper()}"
    
    fig = interaction_plot(x=df[var1], trace=df[var2], 
                           response=df[result],
                           colors=colors
                           ) 
    
    ax = plt.gca()
    ax.set_ylim([0.0, 0.045])
    
    xticks_locations, xticks = plt.xticks()
    new_labels = []
    for t in xticks:
        label_str = t.get_text()
        new_labels.append(pretty_name(label_str))
    plt.xticks(xticks_locations, new_labels)
    
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend(title=legend_title)
    sns.despine()
    save_path = f'outputs/plots/{expr_var}' if expr_var != 'decision_strat' else f'outputs/plots/{expr_var}s'
    save_fig(f'interaction_plot_{var1}_{var2}_{result}_prod{prod_letter}', save_path, 'interaction')
    plt.close()

def make_four_interaction_plots(anova_all_file, expr_var='dist_mult'):
    ''' Make all four interaction plots, one for each type of product and one for ALL'''
    value_vars = [[], 'product_ratios_a', 'product_ratios_b', 'product_ratios_c']
    prod_letters = ['ALL', 'a', 'b', 'c']
    for value_var, letter in zip(value_vars, prod_letters):
        make_interaction_plot(anova_all_file, var2=expr_var, value_vars=value_var, prod_letter=letter, expr_var=expr_var)
 
def combine_anova_files(main_folder_name):
    '''Create a new csv that has a column "Network" which contains a string corresponding to the
    network combination that produced this result. Network combinations are IB, IW, OB, OW.
    `is_dist_mult` is a boolean determines which files to combine'''
    
    folder_path = f'outputs/final_step/csvs/{main_folder_name}/'
    subfolders = ['itin_ba', 'itin_ws', 'orbis_ba', 'orbis_ws']
    frames = []
    for subfolder in subfolders:
        full_path = folder_path + subfolder + '/anova_' + subfolder + '.csv'
        anova_df = pd.read_csv(full_path)
        short_name = 'itin_ws' if subfolder == 'itin_ws_0.5_rewire' else subfolder
        anova_df['network'] = short_name
        frames.append(anova_df)
    result = pd.concat(frames)
    result.to_csv(folder_path+'anova_all_networks.csv')
        
if __name__ == '__main__':
    path = 'outputs/final_step/csvs/dist_mult/'
    anova_all_file = 'outputs/final_step/csvs/decision_strats/anova_all_networks.csv'
    for spatial in [None, 'itin', 'orbis']:
        anova_over_all_networks('outputs/final_step/csvs/decision_strats/anova_all_networks.csv', 
                                var2='decision_strat', 
                                value_vars=['a'],
                                spatial=spatial)
        
    ### INTERACTION PLOTS
    # make_four_interaction_plots(anova_all_file)
    