import sys
sys.path.append("..")
from experiments.imports import *
import csv, pickle
from experiments.helper_functions import save_fig, get_figure_title_and_shortfn_from_filename
import networkx as nx

#### STYLING OPTIONS
NODE_OPTIONS = {
    "node_size": 100,
    "node_color": "tab:blue",
    "alpha": 0.9}
EDGE_OPTIONS = {
    "edge_color": "tab:gray",
    "width": 1,
    'alpha': 0.9,
}
LABEL_OPTIONS = {
    "font_color": "black",
    'font_size': 12
}


### PART 0: Social network full visualization
def visualize_full_network(G, network_file):
    '''Visualize a given nx graph'''
    fig_title, short_filename = get_figure_title_and_shortfn_from_filename(network_file)
    
    plt.figure()
    pos = nx.circular_layout(G)  # Seed layout for reproducibility
    labels = get_locations_from_labels(nx.get_node_attributes(G, 'label'))
    node_options = {
        "node_size": 100,
        "node_color": "tab:blue",
        "alpha": 0.9}
    edge_options = {
        "edge_color": "tab:gray",
        "width": 1,
        'alpha': 0.9,
    }
    label_options = {
        'labels':labels,
        "font_color": "#A0CBE2",
        'font_size': 10
    }
    nx.draw_networkx_nodes(G, pos, **node_options)
    nx.draw_networkx_edges(G, pos, **edge_options)
    plt.tight_layout()
    plt.axis('off')
    save_fig(f'full_viz_{short_filename}.png', 'outputs', 'network_viz')

def full_visualize_all_networks():
    '''This function will call the viz function for the files needed'''
    filenames = ['itineraries_ba_50', 
                 'itineraries_watts-strogatz_50',
                 'orbis_ba_50',
                 'orbis_watts-strogatz_50']
    for fn in filenames:
        G= pickle.load(open(f'social_networks/{fn}.pickle', 'rb')) 
        visualize_full_network(G, fn)
        graph_edges_using_subgraph(G, 'London', fn)

def get_locations_from_labels(labels):
    '''Input: dictionary of labels, with the key being the node id and the value the label string.
    Label strings in the input are in the format "Location, Agent X"
    This function returns a dictionary where each label string is just the Location name'''
    for k,v in labels.items():
        new_v = v.split(',')[0] if ',' in v else v
        labels[k] = new_v
    return labels
              
def get_node_id_for_label(G, label):
    node_matches = [(id,data) for id,data in G.nodes(data=True) if data['label'].split(',')[0]==label]
    nodes = [match[0] for match in node_matches]
    if len(nodes) > 0:
        return nodes[0]
    else:
        raise NameError(f"Node label {label} not found in graph")
    
def graph_edges_using_subgraph(G, label, network_filename):
    ''' Graph all the edges from a given node (determined by label)'''
    fig_title, short_filename = get_figure_title_and_shortfn_from_filename(network_filename)
    node_id = get_node_id_for_label(G, label)
    edgelist=G.edges(node_id)
    nodelist=list(G.neighbors(node_id)) + [node_id]
    
    plt.figure()
    k = G.subgraph(nodelist)
    
    pos = nx.circular_layout(k, scale=10)
    labels = get_locations_from_labels(nx.get_node_attributes(k, 'label'))
    options = NODE_OPTIONS
    options['node_color'] = 'white'
    options['node_size'] = 2000
    nx.draw_networkx_nodes(k, pos, **options)
    nx.draw_networkx_labels(G, pos, labels=labels, **LABEL_OPTIONS)
    nx.draw_networkx_edges(G, pos, edgelist, **EDGE_OPTIONS)
    plt.tight_layout()
    plt.axis('off')
    plt.savefig(f'outputs/networks/social_net_{short_filename.lower()}_{label}.png')

##############    
## PART 2: Network Metrics
def get_avg(centrality_dict):
    total = sum(centrality_dict.values())
    return total / len(centrality_dict)

def split_on_underscore(filename):
    '''Take a filename in the format [spatial]_[social]_[num_merchants] 
    and return a dictionary with keys-> values'''
    filename = filename[:-(len('.pickle'))]
    split = filename.split("_")
    return {'spatial': split[0], 'social': split[1], 'num_merchants': split[2]}

def get_metrics(G, network_filename):
    '''Returns a dictionary with metrics'''
    network_parts = split_on_underscore(network_filename)
    return {'spatial'       : network_parts['spatial'],
            'social'        : network_parts['social'],
            'num_merchants' : network_parts['num_merchants'],
            'degree_centrality': get_avg(nx.degree_centrality(G)), 
            'closeness_centrality': get_avg(nx.closeness_centrality(G)),
            'network_density': nx.density(G),
            # 'clustering_coeff': nx.clustering(G),
            'sigma': nx.sigma(G, seed=30),
            'omega': nx.omega(G, seed=30),
            }
    
def create_csv_with_network_metrics(num_merchants):
    '''Create one csv with all network metrics, for the networks with the given number of merchants.'''    
    with open(f'outputs/networks/network_metrics_{num_merchants}.csv', 'w') as f:
        w = csv.writer(f)
        should_write_header = True
        for network_filename in os.listdir('social_networks'):
            if 'AGENT_INFO' in network_filename or not f'{num_merchants}' in network_filename:
                pass
            else:
               G= pickle.load(open(f'social_networks/{network_filename}', 'rb')) 
               metrics = get_metrics(G, network_filename)
               if should_write_header:
                   w.writerow(metrics.keys())
                   should_write_header = False
               w.writerow(metrics.values())
               
def visual_centrality(centrality='degree', filename='outputs/networks/network_metrics_800.csv'):
    '''Create a scatter plot with the centrality (either degree or closeness) 
    for each spatial-social combination.
    - `centrality` is 'degree' or 'closeness'
    '''
    plt.figure()
    df = pd.read_csv(filename)
    y = f'{centrality}_centrality'
    df = df.rename(columns={'spatial': 'Spatial Network', 'social': 'Social Network'})
    df['Spatial Network'] = df['Spatial Network'].map({'itineraries': 'Itineraries', 'orbis': 'ORBIS'})
    g = sns.scatterplot(data=df, x='num_merchants', y=y, 
                style='Spatial Network', hue='Social Network')
    plt.xlabel('Number of Merchants')
    plt.ylabel(f'{centrality.title()} Centrality')
    plt.legend(bbox_to_anchor=(1,1), loc=1, borderaxespad=0)
    sns.despine()
    
    save_fig(f'plot_{y}', 'outputs', 'networks')
    plt.close()
    
if __name__ == '__main__':
    ### VISUALS
    network_filename = 'orbis_watts-strogatz_50'
    G= pickle.load(open(f'social_networks/{network_filename}.pickle', 'rb'))

    # visualize_full_network(G, network_filename)
    # full_visualize_all_networks()
    
    # location = 'London'
    # for centrality in ['degree', 'closeness']:
    #     visual_centrality(centrality=centrality)
    
    # graph_edges_using_subgraph(G, location, network_filename)
    
    ############################################################################
    ### METRICS
    # create_csv_with_network_metrics(200)
    
    