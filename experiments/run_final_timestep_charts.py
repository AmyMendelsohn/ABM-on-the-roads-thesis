from experiments.imports import *
from experiments.helper_functions import pretty_name, save_fig, create_figure_title

# This file has functions that create graphs related to the distributions at the
# final timestep. It has the Mercury-style charts, and the total product over 
# all locations chart. 

#******************************************************************************#
# MERCURY-style charts

def final_timestep_presence_counts(df, title, filename, subfolder=None):
    ''' This function creates the "Mercury-style chart", and is called in the 
    `mercury_style_charts` function.
    
    Create a bar chart with the number of locations with at least one of each 
    product type. 
    - df: final_timestep df
    - title: title string with variables
    - filename with id_num
    - subfolder where the file goes (the section after `outputs/final_step`)'''
    plt.figure()
    
    # Sum up all of the product of each type (ie group by Variable column in melted df)
    df = df[df['value'] > 0]
    # Convert any value present into a 1
    df['value'].values[:] = 1
    df.groupby('variable').sum()
    g = sns.histplot(df, x='variable', hue='variable', palette='colorblind')
    
    plt.ylim(0, 30)
    plt.ylabel('Number of locations')
    plt.xlabel('')
    g.set_xticklabels(['Product A', 'Product B', 'Product C'])
    plt.legend().remove()
    
    first_title_line = "Number of locations with pottery present"
    if title is None or title == '':
        full_title = first_title_line
    else:
        full_title = first_title_line +"\n" + title
    # g.set_title(full_title)
    sns.despine()
    
    save_fig_final_step(filename, output_path, subfolder)
    plt.close()

def mercury_style_charts(file, df, title, id_num, filename, subfolder=None):
    '''Create simple bar charts.
    - `subfolder`: subfolder to create in `final_step` folder if it doesn't exist.
    None if there is no subfolder'''
    product_types = ["PRODUCT_A Product", "PRODUCT_B Product", "PRODUCT_C Product"]
    locations_df = get_locations_final_df(file, df)
    selected = locations_df[['agent_stable_id'] + product_types].copy()
    melted = selected.melt(id_vars=['agent_stable_id'])
    # Create bar chart that has presence and absence of product at the final timestep
    final_timestep_presence_counts(melted, title, f"PRESENCE_{filename}", subfolder)

    
def run_function_over_folder(func, folderpath, exp='dist_mult'):
    '''given a string name corresponding to a graphing function (like "Mercury" or "Final Product"),
    this function runs that function over all csvs in the given folderpath, recursively.
    It creates folders to match the folder(s) it reads from.'''
    for root, dirs, files in os.walk(folderpath):
        subfolder = root.split('outputs/csv_results/')[-1]
        include_decision_strat = True if 'decision_strat' in subfolder else False
        id_num = 0
        for file in sorted(files):
            folder = f"{pretty_name(file.split('_')[0])}_{pretty_name(file.split('_')[1])}"
            dir =  f'outputs/final_step/{exp}/{folder.lower()}'
            
            if not os.path.exists(dir):
                os.makedirs(dir)  
            new_file = f"TOTALS_{file.split('.csv')[0]}.png"
            if '400.csv' in file and new_file not in os.listdir(dir):
                title = create_figure_title(file, include_decision_strat)
                full_filepath = os.path.join(root, file)
                
                if func == 'mercury':
                    mercury_style_charts(file=full_filepath, 
                                        df=None, 
                                        title=title, 
                                        id_num=id_num, 
                                        filename=f'{file.split("/")[-1].strip(".csv")}',
                                        subfolder=subfolder)
                elif func == 'final product':
                    final_timestep_charts(file=full_filepath, 
                                          df=None, 
                                          title=title, 
                                          id_num=id_num, 
                                          filename=f'{file.split("/")[-1].strip(".csv")}',
                                          subfolder=subfolder)
                    
                id_num += 1

def run_all_charts_for_folder(foldername='dist_mult'):
    path_to_data = f'outputs/csv_results/{foldername}/'
    for folder in os.listdir(path_to_data):
        if folder == '.DS_Store':
            continue
        print('folder:' , folder)
        full_path = f'{path_to_data}/{folder}'
        run_function_over_folder("mercury", full_path, exp=foldername)
        run_function_over_folder("final product", full_path, exp=foldername)         
        
        
    
### PART 2: Final timestep locations histogram. The chart is created in the 
### `final_timestep_charts()` function.

def get_top_10_locations(file, df=None):
    if df is None:
        df = pd.read_csv(file)
    final_timestep_df = df[df['Step'] == df['Step'].max()]
    locations = final_timestep_df[final_timestep_df['agent_category']=='location'].copy()
    locations = locations[['RunId', 'Step', 'agent_stable_id', 'agent_location', 'modern_name', 'node_degree','PRODUCT_A Product', 'PRODUCT_B Product', 'PRODUCT_C Product']]
    locations = locations.groupby(['modern_name']).mean()
    locations = locations.sort_values('PRODUCT_A Product', ascending=False)
    return locations.head(10)

def get_locations_final_df(file, df=None):
    if df is None:
        df = pd.read_csv(file)
    final_timestep_df = df[df['Step'] == df['Step'].max()]
    locations = final_timestep_df[final_timestep_df['agent_category']=='location'].copy()
    locations = locations[['RunId', 'Step', 'agent_stable_id', 'agent_location', 'modern_name', 'node_degree','PRODUCT_A Product', 'PRODUCT_B Product', 'PRODUCT_C Product']]
    
    locations = locations.reset_index()
    
    # Get total product (sum of all types)
    frames = []
    for prod in ['A', 'B', 'C']:
        product = f'PRODUCT_{prod} Product'
        total = locations.groupby(['RunId'])[product].sum()
        total = total.repeat(len(locations['agent_stable_id'].unique())).reset_index()
        total = total.reset_index()
        frames.append(total[product])
    total = pd.concat(frames, axis=1).sum(1)
    
    # Set ratios for each product
    for prod in ['A', 'B', 'C']:  
        product = f'PRODUCT_{prod} Product'
        locations[product] = locations[product] / total
        locations[product] = locations[product].fillna(0)
    
    locations = locations.groupby(['modern_name']).mean()
    return locations.reset_index()
    

def final_timestep_product(df: pd.DataFrame, title, filename, name_col, subfolder=None):
    '''Create a histogram, with locations sorted by degree, and amount of product.
    Name_col is a string, either 'modern_name' or 'latin_name' '''
    df = df.sort_values(by=['node_degree'], ascending=False )
    if "orbis" in title:
        plt.figure(figsize=(6,7))
    else:
        plt.figure(figsize=(13,6))
    plt.ylim(0, 0.4)
    
    melted = df.melt(id_vars=[name_col], value_name='product')
    melted = melted[melted['variable'] != 'node_degree']
    ax = sns.histplot(melted, x=name_col, hue='variable', weights='product',
                multiple='stack', shrink=0.8, palette="colorblind", legend=True)
    
    ax.legend_.set_title('Product Type')
    for old in ax.legend_.texts:
        label_str = old.get_text()
        product_type = label_str.split(' ')[0][-1]
        new_label = f'Product {product_type}'
        old.set_text(new_label)
        
    ax.set_ylabel('Proportion of total product')
    
    plt.xticks([i for i in range(len(df[name_col]))])
    
    xtick_labels = ax.get_xticklabels()
    for i, label in enumerate(xtick_labels):
        label_str = label.get_text()
        if 'PRODUCT' in label_str:
            product_type = label_str.split(' ')[0][-1]
            new_label = ''.join(label_str.split(' ')[1:])
            xtick_labels[i] = f'{new_label} ({product_type})'
    ax.set_xticklabels(labels=xtick_labels, rotation=90)
    
    ax.set_xlabel('Locations')
    # ax.set_title("Amount of pottery at the final timestep \n" + title)
    plt.tight_layout()
    sns.despine()
    
    save_fig_final_step(filename, output_path, subfolder)
    plt.close()
    
def final_timestep_agents(df: pd.DataFrame, title, filename):
    '''Create a histogram, with locations sorted by degree, and number of agents'''
    df = df.sort_values(by=['node_degree'], ascending=False)
    location_count_df = df.groupby('agent_location').count().reset_index()[['agent_location', 'RunId']]
    location_count_df.rename({'RunId': 'count'},axis=1, inplace=True)
    
    if "orbis" in title:
        plt.figure()
    else:
        plt.figure(figsize=(13.5,6))
    
    ax = sns.histplot(location_count_df, x='agent_location', hue='count', weights='count', binwidth=1, shrink=0.8)
    ax.set_ylabel('number of merchants')
    
    plt.xticks([i for i in range(len(location_count_df['agent_location']))])
    ax.set_xticklabels(labels=location_count_df['agent_location'], rotation=90)
    ax.set_title("Number of agents \n" + title)
    plt.tight_layout()
    output_folder = f'{output_path}/final_step'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(f'{output_folder}/{filename}.png')
    # plt.show()
    plt.close()


def final_timestep_charts(file, df, title, id_num, filename, subfolder=None):
    ''' Function to create final timestep charts that are NOT from MERCURY.
    - Create a heatmap of locations and total amount of product, locations sorted by degree'''
    product_types = ["PRODUCT_A Product", "PRODUCT_B Product", "PRODUCT_C Product"]
    locations_df = get_locations_final_df(file, df)
    name_col = 'modern_name'
    selected = locations_df[[name_col] + product_types + ['node_degree']].copy()
    final_timestep_product(selected, title, f"TOTALS_{filename}", name_col, subfolder)

## HELPER FUNCTIONS
def save_fig_final_step(filename, output_path, subfolder):
    '''Creates a new folder if necessary and saves a figure with the given filename.
    Uses the helper_functions.py save_fig'''
    save_fig(filename, f'{output_path}/final_step', subfolder)
    
def location_degree_dist(df):
    plt.figure()
    g = sns.histplot(df, x='node_degree')    
    plt.show()
    plt.close()
    
def get_agents_final_df(file, df):
    if df is None:
        df = pd.read_csv(file)
    final_timestep_df = df[df['Step'] == df['Step'].max()]
    return final_timestep_df[final_timestep_df['agent_category']!='location'].copy()
        
        
# if __name__ == '__main__':
    # df = get_top_10_locations(file='outputs/final_step/csvs/dist_mult/itin_ba/itineraries_ba_node degree_400_0_(1, 0, 0)_30_400.csv')
    # print(df)
    # df.to_csv('./outputs/top10/400_0.csv')
    
    # df = get_top_10_locations(file='outputs/final_step/csvs/dist_mult/itin_ba/itineraries_ba_node degree_400_1_(1, 0, 0)_30_400.csv')
    # print(df)
    # df.to_csv('./outputs/top10/400_1.csv')
    # product_over_time_one_location(FILE, 'London')