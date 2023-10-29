import sys
sys.path.append("..")

from experiments.imports import *
from experiments.helper_functions import normalize, save_fig, pretty_name, set_xticks

# FILE INFO: Create figures that use ANOVA csv files.
# - boxplots
# - heatmaps

##### BOXPLOTS

## CORE
def create_boxplot_core_code(x, x_label, y, y_label, hue, legend_title, fig_title,
                             num_merchants, all_anova_file, df=None):
    if df is None:
        df = pd.read_csv(all_anova_file)
        df['product_ratios'] = df['product_amount'] / df['total_product_in_system']
        df = normalize(df, 'product_ratios')
        
        if num_merchants != None:
            df = df[df['num_merchants'] == num_merchants]

    fig, ax = plt.subplots()
    sns.boxplot(x=x, y=y, data=df, hue=hue, palette="Blues", 
                # showmeans=True,
                # meanprops={'marker':'o',
                #        'markerfacecolor':'white', 
                #        'markeredgecolor':'black',
                #        'markersize':'8'}
                )
    
    set_xticks(ax)
    ax = plt.gca()
    ax.set_ylim([0.0, 1])
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend(title=legend_title)
    sns.despine()
    
   
## Code to create specific boxplots
def create_boxplot_product_by_num_merchants(network, expr_var):
    '''Create a boxplot with the number of merchants on the X axis, and
    proportion of total product on the Y axis. The hue is the distance multiplier.
    `network` is a string, like 'itin_ba'.
    - expr_var is the experiment variable (dist_mult or decison_strat)
    '''
    ## VARIABLES
    x, x_label = 'num_merchants', 'Number of Merchants'
    y, y_label = 'product_ratios', 'Product Ratios'
    hue, legend_title = 'dist_mult', 'Distance Multiplier'
    anova_filepath = f'outputs/final_step/csvs/dist_mult/{network}/anova_{network}.csv'
    
    fig_title = f'Product A in London ({pretty_name(network)})'
    create_boxplot_core_code(x, x_label, y, y_label, hue, legend_title, fig_title, 
                             num_merchants=None, all_anova_file=anova_filepath)
    save_path = f'outputs/plots/{expr_var}'
    save_fig(f'product_by_num_merchants_distance_{network}', save_path, 'boxplots')
    plt.close()

def create_boxplot_product_by_dist(all_anova_file, num_merchants, expr_var):
    '''Create a boxplot for part 2-d'''
    ## VARIABLES
    x, x_label = 'network', 'Network'
    y, y_label = 'product_ratios', 'Proportion of Total Product A'
    hue, legend_title = 'dist_mult', 'Distance Multiplier'
    fig_title = 'Proportion of total Product A in London'
    create_boxplot_core_code(x, x_label, y, y_label, hue, legend_title, fig_title, 
                             num_merchants, all_anova_file)
    save_path = f'outputs/plots/{expr_var}'
    save_fig(f'product_by_network_and_distance_{num_merchants}', save_path, 'boxplots')
    plt.close()

def create_boxplot_product_by_decision_strats(all_anova_file, num_merchants, expr_var):
    '''Create a boxplot for part 2-d'''
    ## VARIABLES
    x, x_label = 'network', 'Network'
    y, y_label = 'product_ratios', 'Proportion of Total Product'
    hue, legend_title = 'decision_strat', 'Decision Strategy'
    fig_title = 'Ratio of total Product A in London'
    create_boxplot_core_code(x, x_label, y, y_label, hue, legend_title, fig_title, 
                             num_merchants, all_anova_file)
    plt.legend(loc='upper right', title=legend_title)
    
    save_path = f'outputs/plots/{expr_var}'
    save_fig(f'product_by_network_and_strategy_{num_merchants}', save_path, 'boxplots')
    plt.close()

def boxplot_prod_by_type_and_distmult(all_anova_file, num_merchants, network, expr_var):
    '''Create a boxplot for part 2-b.
    - Network is either itin_ba, itin_ws, orbis_ba, orbis_ws, or None (for all networks).
    - expr_var is the experiment variable (dist_mult or decison_strat)'''
    ## VARIABLES
    x, x_label = 'product_type', 'Product Type'
    y, y_label = 'product_ratios', 'Proportion of Total Product'
    hue, legend_title = 'dist_mult', 'Distance Multiplier'
    fig_title = 'Ratio of total products in London'
    
    ## Core code, but with the dataframe melted.
    df = manipulate_all_anova_file(all_anova_file, num_merchants, network)

    if num_merchants == 200 and network == 'itin_ba':
        print(df['product_ratios'].mean())
    create_boxplot_core_code(x, x_label, y, y_label, hue, legend_title, fig_title, 
                             num_merchants, all_anova_file, df)
    plt.legend(title=legend_title)
    
    
    save_path = f'outputs/plots/{expr_var}'
    save_fig(f'product_by_type_and_distmult_{num_merchants}_{network}', save_path, 'boxplots')
    plt.close()


##### HEATMAPS

def create_four_heatmaps(path, x_var, x_label, agg_type):
    '''Runner function to create heatmaps for the 4 networks
        create_four_heatmaps(path = 'outputs/final_step/csvs/decision_strats', 
                         x_var='decision_strat',
                         x_label='Decision Strategy')
    '''
    if 'dist' in x_var:
        if 'var' in agg_type:
            vmin, vmax = 0, 0.055
        else:
            vmin, vmax = 0.1, 0.95
    elif 'var' in agg_type:
        vmin, vmax = 0, 0.15
    else:
        vmin, vmax = 0.09, 0.39
    
    for folder in os.listdir(path):
        if folder != '.DS_Store' and '.csv' not in folder and 'no_rewiring' not in folder:
            csv = f'{path}/{folder}/anova_{folder}.csv'
            print(folder)
            heatmap_prod_for_num_merchants_by_x(csv, 'A', x_var, x_label, vmin=vmin, vmax=vmax, agg_type=agg_type)
  
def heatmap_prod_for_num_merchants_by_x(csv, prod_type='A',x_var='dist_mult', x_label='Distance Multiplier',
                                        vmin=0, vmax=1, agg_type='mean'):
    '''Create a heatmap with number of merchants on y axis, `x_var` on x (ie 'dist_mult'), 
    and the amounts are the amount of product of the given product type.
    Inputs: `csv`, which is a anova_file csv
            `prod_type` the type of product (not used)
            `vmin` and `vmax`: min and max for scale
            `agg_type`: the type of aggregation used, either 'mean', 'median', or 'var'
    '''
    plt.figure()
    spatial = csv.split('_')[-2]
    social = csv.split('_')[-1].split('.csv')[0].upper()
    if spatial == 'orbis':
        spatial = 'ORBIS'
    elif spatial == 'itin':
        spatial = 'itin'
    elif '0' in social or social == '1':
        # handle three part folder names, ie `orbis_ws_1`
        spatial = csv.split('_')[-3]
        social = csv.split('_')[-2].split('.csv')[0].upper()
    else:
        spatial = '??'
        social = '??'
    # Recall that the anova files have a product_amount, which by default is ProductA
    df = pd.read_csv(csv)
    # Add ratio column
    df['product_ratios'] = df['product_amount'] / df['total_product_in_system']
    # Normalize ratio column
    df = normalize(df, 'product_ratios')
    # create a DF with averaged values for each dist_mult and num merchants combination
    df = df.groupby(['num_merchants', x_var], as_index=False).agg(agg_type)
    df = df.pivot(columns=x_var, index='num_merchants', values='product_ratios')
    fig = sns.heatmap(data=df, annot=True, linewidth=.5, cmap="mako", vmin=vmin, vmax=vmax)
    
    # plt.title(f'Ratio of Total Product in London')
    plt.xlabel(x_label)
    plt.ylabel('Number of Merchants')
    plt.tight_layout()
    save_path = f'outputs/plots/{x_var}' if x_var != 'decision_strat' else f'outputs/plots/{x_var}s'
    save_fig(f'heatmap_{spatial.lower()}_{social.lower()}_{agg_type}', save_path, f'heatmaps')
    plt.close()
    
## HELPER FUNCTIONS (see also helper_functions.py)    
def manipulate_all_anova_file(all_anova_file, num_merchants=200, network='itin_ba'):
    '''
    ** ONLY FOR DIST_MULT ** 
    Modify the csv file so that it is ready to be used in a boxplot with the types of product on 
    the x-axis, and differences in distance multipliers for the hue, and normalized product ratio for y-axis.
    Return a df.'''
    df = pd.read_csv(all_anova_file)
    df['product_ratios'] = df['product_amount'] / df['total_product_in_system']
    df['product_ratios_b'] = df['product_amount_b'] / df['total_product_in_system']
    df['product_ratios_c'] = df['product_amount_c'] / df['total_product_in_system']
    df = normalize(df, 'product_ratios')
    df = normalize(df, 'product_ratios_b')
    df = normalize(df, 'product_ratios_c')
    df = df[df['num_merchants'] == num_merchants]
    if network != None:
        df = df[df['network']==network]
    
    df = pd.melt(df, id_vars=['dist_mult'], 
                 value_vars=['product_ratios', 'product_ratios_b','product_ratios_c'],
                 var_name='product_type',
                 value_name='product_ratios')
    return df

### Functions to all over a set (all num_merchants, all networks)
def call_for_all_networks(func, num_merchants=200, 
                          all_anova_file='outputs/final_step/csvs/dist_mult/anova_all_networks.csv',
                          just_network=False,
                          expr_var='dist_mult'):
    '''pass in a function to call for all four spatial-social networks'''
    for network in ['itin_ba', 'itin_ws', 'orbis_ba', 'orbis_ws', None]:
        if just_network:
            if network is not None:
                func(network, expr_var=expr_var)
        else:
            func(all_anova_file, num_merchants=num_merchants, network=network, expr_var=expr_var)

def call_for_all_num_merchants(func, all_anova_file, expr_var):
    '''call the function for all number of merchants'''
    for n in [50,200,400]:
        func(all_anova_file=all_anova_file, num_merchants=n, expr_var=expr_var)
        
if __name__ == '__main__':
    all_anova_file = 'outputs/final_step/csvs/dist_mult/anova_all_networks.csv'
    # create_boxplot_product_by_decision_strats(all_anova_file, num_merchants=400)
    # create_four_heatmaps(path ='outputs/final_step/csvs/decision_strats', 
    #                     x_var='decision_strat',
    #                     x_label='Decision Strategy')
    # create_boxplot_product_per_type_by_distmult(all_anova_file='outputs/final_step/csvs/dist_mult/anova_all_networks.csv', 
    #                                             num_merchants=200,
    #                                             network='orbis_ws')
    # create_boxplot_num_merchants_by_product_amt()
    # create_boxplot_product_by_dist(all_anova_file, 400)
    
    # boxplot_prod_by_type_and_distmult(all_anova_file, 400, 'itin_ba', 'dist_mult')
    
    