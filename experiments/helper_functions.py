from ABM.constants import ITINERARIES, ORBIS, BA_GRAPH, WATTS_GRAPH
from experiments.imports import *

# A file for formatting helper functions.



### From figures_anova_boxplot.py
def normalize(df, column_name):
    '''Helper function that normalizes a column in a dataframe.'''
    result = df.copy()
    max_value = df[column_name].max()
    min_value = df[column_name].min()
    result[column_name] = (df[column_name] - min_value) / (max_value - min_value)
    return result


## Saving and naming
def save_fig(filename, output_folder, subfolder):
    '''Creates a new folder if necessary and saves a figure with the given filename.'''
    if subfolder:
        output_folder = f'{output_folder}/{subfolder}'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(f'{output_folder}/{filename}.png') 

def get_full_filepath(fn):
    'Return a string with the full filepath to the given file'
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(fn)))
    return os.path.join(__location__, fn)
           
def pretty_name(label):
    pretty_names = {
        'itin_ba': 'Itineraries BA',
        'itin_ws': 'Itineraries WS',
        'orbis_ba': 'ORBIS BA',
        'orbis_ws' :'ORBIS WS',
        'product_ratios': 'Product A',
        'product_ratios_b': 'Product B',
        'product_ratios_c': 'Product C',
        'decision_strat': 'Decision Strategy',
        'dist_mult': 'Distance Multiplier',
        'network': 'Network',
        'ba': 'BA', 
        'watts-strogatz': 'WS',
        'itineraries': 'itin'
    }
    # Convert names like itin_ba_1 to itin_ba
    if len(label.split('_')) == 3 and ('ba' in label or 'ws' in label):
        label = '_'.join(label.split('_')[:-1])
    if label in pretty_names:
        return pretty_names[label]
    return label  

def set_xticks(ax):
    '''Set xticks to use pretty names'''
    xticks = ax.get_xticklabels()
    new_labels = []
    for t in xticks:
        label_str = t.get_text()
        new_labels.append(pretty_name(label_str))
    ax.set_xticklabels(new_labels)

def convert_to_folder_name(spatial, social):
    '''Return a folder name in the correct format, ie `itin_ba`.
    - `spatial`: a spatial network like ITINERARIES from constants
    - `social`: a social network like BA_GRAPH'''
    spatial_formatted = 'itin' if spatial == ITINERARIES else 'orbis'
    social_formatted = 'ba' if social == BA_GRAPH else 'ws'
    return f'{spatial_formatted}_{social_formatted}'

# Figure titles
def create_figure_title(filename, include_decision_strat=False):
    '''Return a figure title in the format: 
    {spatial_net}, {social_net}, {num_merchants} Merchants, Decision Strategy = {dec_strat}.
    Used in final timestep charts.'''
    parts = filename.split('_')
    spatial_net, social_net, num_merchants, dec_strat = parts[0], parts[1], parts[3], parts[5]
    spatial_net = spatial_net[0].upper() + spatial_net[1:]
    social_net = social_net.upper()
    
    title = f'{spatial_net}, {social_net}, {num_merchants} Merchants'
    if include_decision_strat:
        title += f', Decision Strategy = {dec_strat}'
    return title

def get_figure_title_and_shortfn_from_filename(fn):
    '''Convert filenames like `orbis_watts-strogatz_50` into a figure title,
    and also a short filename like `orbis_ws_50`. 
    First used in network_graphs.py'''
    num_merchants = fn.split('_')[-1]
    spatial = fn.split('_')[0]
    spatial = spatial.upper() if spatial == ORBIS else spatial.title()
    social = fn.split('_')[1]
    social = 'WS' if WATTS_GRAPH in social else 'BA'
    return f'{spatial} {social}, {num_merchants} merchants', f'{spatial}_{social}_{num_merchants}'   