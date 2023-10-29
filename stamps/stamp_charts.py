import pandas as pd 
import os 
import seaborn as sns
import matplotlib.pyplot as plt


def get_prod_per_site_from_final_step(file, averaging=True):
    ''' Takes a file path to a final_step file, and returns a df with a ratios column for each location showing 
    the proportion of total product at that location.
    >>> file = '../experiments/outputs/final_step/csvs/dist_mult/itin_ba/itineraries_ba_node degree_200_0.1_(1, 0, 0)_30_400.csv'
    >>> get_prod_per_site_from_final_step(file)'''
    df = pd.read_csv(file)
    if averaging:
        df = df.groupby(['agent_location']).mean(numeric_only=True).reset_index()
    else:
        df = df.groupby(['agent_location'])
    melted = df.melt(id_vars=['agent_location', 'num_merchants', 'distance_multiplier'], value_vars=['PRODUCT_A Product'],value_name='product')
    melted = melted[melted['variable'] != 'node_degree']
    product = melted['product'].fillna(0)
    total = product.sum()
    melted['total_product'] = total
    melted['ratios'] = melted['product'] / melted['total_product']
    return melted

def draw_ratios_histogram(df, f1, network_type, graph_type):
    '''
    - f1 is something like `dist_mult`
    - f2 is something like `itin_ba`
    '''
    filename = f'ratios_{graph_type}_{network_type}'
    if network_type == 'stamps':
        if graph_type == 'stripplot':
            g = sns.stripplot(df, x='ratios', legend='full')
        elif graph_type=='hist':
            g = sns.histplot(df, x='ratios', bins=60, legend='full')
            
    else: 
        if graph_type == 'stripplot':
            g = sns.stripplot(df, x='ratios', legend='full', hue='distance_multiplier', palette='colorblind')
            plt.legend(title='Distance Multiplier')      

        elif graph_type =='hist':
            g = sns.histplot(df, x='ratios', bins=60, palette='colorblind')
            # plt.legend(title='Distance Multiplier')      
            
    sns.despine()
              
    g.set_xlabel('Proportion of product at location')
    g.set_ylabel('Number of locations')
    
    output_folder = f'../experiments/outputs/stamps/'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(f'{output_folder}/{f1}_{filename}.png')    
    plt.close()    
    
    
def make_individual_ratios_histograms_for_folder(folder_path):
    '''Given a folder path like '../experiments/outputs/final_step/csvs/dist_mult', go through all subfolders (ie 'itin_ba', 'itin_ws') 
    and make a ratios histogram for each final step file. Save it to a folder in outputs called stamps.'''
    f1 = folder_path.split('/')[-1]
    for subfolder in os.listdir(folder_path):
        if subfolder != '.DS_Store' and not 'anova' in subfolder:
            
            for filename in os.listdir(f'{folder_path}/{subfolder}'):
                if filename.endswith('.csv') and not 'anova' in filename and filename != '.DS_Store':
                    full_name = f'{folder_path}/{subfolder}/{filename}'
                    df = get_prod_per_site_from_final_step(full_name)
                    draw_ratios_histogram(df, f1=f1, f2=subfolder, filename=filename)
                    
def make_folder_ratios_dfs(folder_path):
    '''Given a folder path like '../experiments/outputs/final_step/csvs/dist_mult', go through all subfolders (ie 'itin_ba', 'itin_ws') 
    and make ONE ratios df for each subfolder, ie 'itin_ba'. Save it to a folder in outputs called stamps.'''
    f1 = folder_path.split('/')[-1]
    dfs = {}
    for subfolder in os.listdir(folder_path):
        frames = []
        if subfolder != '.DS_Store' and not 'anova' in subfolder:
            
            for filename in os.listdir(f'{folder_path}/{subfolder}'):
                if filename.endswith('.csv') and not 'anova' in filename and filename != '.DS_Store':
                    full_name = f'{folder_path}/{subfolder}/{filename}'
                    df = get_prod_per_site_from_final_step(full_name, averaging=True)
                    frames.append(df)
                    
            subfolder_df = pd.concat(frames)
            dfs[subfolder] = subfolder_df
    return dfs


##### STAMP DATA    
def get_britain_df():
    '''Returns a df from the stamp file, only with sites in Britain'''
    df = pd.read_csv('stamps-xrubio-ecology-of-roman-trade.txt', delimiter=';')
    b_df = df[df['name'] == 'Britannia']
    b_df = b_df.reset_index(drop=True)
    b_df = b_df[[ 'lat', 'long', 'type', 'site', 'code', 'id',]]
    b_df = b_df.rename(columns={'id': 'xrubio_id'})
    return b_df
    
def create_prod_per_site_data(df, pottery_type='Dressel 20', site_col_name='site'):
    '''Create a dataframe with product amount per site, from xrubio data (originally). '''
    
    if pottery_type == 'Dressel 20':
        df = df[df['type']==pottery_type]

    # Convert a csv with one row per item to something with one line per site, with number of product per site
    df['counts'] = df.groupby(site_col_name)[site_col_name].transform('count')
    prod_per_site = pd.DataFrame(df.groupby(site_col_name).first())
    prod_per_site = prod_per_site.reset_index()
    prod_per_site = prod_per_site[[site_col_name, 'counts']]
    return prod_per_site

def prod_per_site_ratios(df, to_csv=False):
    ''' Starting from the prod_per_site df, create a similar one with ratios'''
    total = df['counts'].sum()
    df['ratios'] = df['counts'] / total
    if to_csv:
        df.to_csv('brittania_stamps_prod_per_site.csv', index=False)
    return df

#### MAKE ALL
def make_all_ratio_charts():
    graph_types = ['stripplot', 'hist']
    stamp_df = get_britain_df()
    prod_per_site = create_prod_per_site_data(df = stamp_df, pottery_type='Dressel 20')
    df = prod_per_site_ratios(prod_per_site, to_csv=False)
    for g in graph_types:
        draw_ratios_histogram(df=df, f1='stamp_data', network_type='stamps', graph_type=g)
        draw_ratios_histogram(df=df, f1='stamp_data', network_type='stamps', graph_type=g)
    dfs = make_folder_ratios_dfs(folder_path)
    for foldername, df in dfs.items():
        for g in graph_types:
            draw_ratios_histogram(df=df, f1=foldername, network_type=foldername, graph_type=g)
            draw_ratios_histogram(df=df, f1=foldername, network_type=foldername, graph_type=g)
    
    
if __name__ == '__main__':
    folder_path = '../experiments/outputs/final_step/csvs/dist_mult'
    full_name = f'{folder_path}/itin_ba/itineraries_ba_node degree_200_0.1_(1, 0, 0)_30_400.csv'
    # df = get_prod_per_site_from_final_step(full_name)
    # make_folder_ratios_histograms(folder_path)
    make_all_ratio_charts()

    
    