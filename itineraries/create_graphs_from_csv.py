from collections import defaultdict
import networkx as nx 
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
sys.path.append("..")
from ABM.constants import MAC
import csv

######################
# HOW TO USE
#
# - If this is the first time creating, then run 


def get_locations_and_distances_lists(filename):
    ''' Return a list of latin names, modern names, and distances '''
    locations_pd = pd.read_csv(filename, skipinitialspace=True)
    # Use "higher confidence" column
    locations_pd = locations_pd[locations_pd['Higher Confidence'] != ''].copy()
    locations_pd = locations_pd[locations_pd['Higher Confidence'].notna()].copy()
    locations_pd = locations_pd[locations_pd['Roman Miles'].map(lambda x: isinstance(x, int) or x.isnumeric())].copy()
    # locations_pd.to_csv('filtered_locations_20230831n.csv', mode='a', header=False)
    # Locations will be a list of (latin, modern) tuples
    latin_names = list(locations_pd['Itinerary Text'])
    
    # modern_names = list(locations_pd['Identification'])
    modern_names = list(locations_pd['Higher Confidence'])
    
    distances = list(locations_pd['Roman Miles'].astype(int))[1:]

    return latin_names, modern_names,  distances

def create_locations_csv(filename):
    '''write a csv with all locations (latin/modern names) in the given file'''
    df = pd.read_csv(filename, skipinitialspace=True)
    locations = df[['Itinerary Text', 'Identification']]
    locations = locations.rename(columns={'Itinerary Text': 'latin',
                                          'Identification': 'modern'})
    name = filename.strip('csv')
    name = name.strip('.')
    locations.to_csv(f'{name}_locations.csv')

def get_edges_and_edgebunches(locations, distances):
    edges = []
    edgebunches = []
    for index, loc in enumerate(locations[:len(locations) - 1]):
        edges.append([loc, locations[index+1]])
        ebunch = (loc, locations[index+1], distances[index])
        edgebunches.append(ebunch)
    return edges, edgebunches

def get_edge_labels(edges, distances):
    edge_labels = {}
    for index, edge in enumerate(edges):
        edge_labels[tuple(edge)] = distances[index]

def draw_graph(edgebunches, edge_labels):
    G = nx.Graph()
    G.add_weighted_edges_from(edgebunches)
    pos = nx.spring_layout(G)
    plt.figure()
    nx.draw(
        G, pos, edge_color='black', width=1, linewidths=1,
        node_size=500, node_color='pink', alpha=0.9,
        labels={node: node for node in G.nodes()}
    )
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.show()

def get_info_from_csv(filename):
    ''' Extract a tuple of (locations, distances, edgebunches) from a single csv file'''
    l_names, m_names, distances = get_locations_and_distances_lists(filename)
    _, edgebunches = get_edges_and_edgebunches(m_names, distances)
    return l_names, m_names, distances, edgebunches

def get_info_from_all_csv(spatial_dir : str):
    ''' Iterate through all csv files in the correct folder'''
    latin_locations, modern_locations, distances, edgebunches = [], [], [], []
    # filename = r'C:\Users\Amyme\school\2022-S2\MCS-thesis\mesa-explore\basic-model\itineraries\itineraries-files\iter-1-parsed.csv'
    # dir = r'C:\Users\Amyme\school\2022-S2\MCS-thesis\mesa-explore\basic-model\itineraries\itineraries-files'
    # dir = r'C:\Users\Amyme\school\2022-S2\MCS-thesis\mesa-explore\basic-model\itineraries\simple-1'
    for filename in os.listdir(spatial_dir):
        if MAC:
            connector = '/'
        else:
            connector = '\\'
        l_names, m_names, dist, edgebunch = get_info_from_csv(spatial_dir + connector + filename)
        latin_locations.extend(l_names)
        modern_locations.extend(m_names)
        distances.extend(dist)
        edgebunches.extend(edgebunch)
    return (latin_locations, modern_locations, distances, edgebunches)

################################################################################
####### Approach to create a single filtered file.
###########
def get_locations_dists_all_itin(filepath):
    '''Return one dictionary of modern names to latin names.'''
    df = pd.read_csv(filepath)
    latin_locations = list(df['Itinerary Text'])
    modern = list(df['Higher Confidence'])
    
    modern_to_latin = defaultdict(str)
    for i, modern_name in enumerate(modern):
        modern_to_latin[modern_name] = latin_locations[i]
        
    return modern_to_latin

def get_edgebunches_separate_itineraries(filepath):
    '''Return a list of edgebunches corresponding to itinerary connections.
    There are no "false" connections, ie all of these are genuinely in the itineraries,
    starting from a filtered CSV file (given with full filepath) of all 
    itinerary positions, names, and distances.'''
    edgebunches = []
    modern_string = 'Higher Confidence'
    distance_string = 'Roman Miles'
    # distance_string = 'Modified Distances Rounded'
    with open(filepath, 'r') as fp:
        reader = csv.DictReader(fp)
        prev_row = []
        for curr_row in reader:
            is_start = curr_row['Position'] == '1'
            # If this Itinerary is the same as the previous, now add an edgebunch
            if not is_start and curr_row['Itinerary'] == prev_row['Itinerary']:
                start, end, cost = prev_row[modern_string], curr_row[modern_string], float(curr_row[distance_string])
                ebunch = (start, end, cost)
                edgebunches.append(ebunch)
            # if this is the first in an itinerary, then just save the row and move on.
            prev_row = curr_row
        return edgebunches

def filter_itinerary(filename, fields):
    '''Given a filepath like `iter-1-parsed.csv`, this function returns a list of dictionaries,
       where each dictionary is one row of a filtered itinerary file.'''
    dashes = filename.split('-')
    itinerary_num = dashes[len(dashes) - 2]
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        filtered_rows = []
        pos = 1
        is_after_remove = False
        for row in reader:
            filtered_row = {}
            if row['Higher Confidence'] != '' and row['Roman Miles'].isnumeric():
                for field in fields:
                    if field == 'Itinerary':
                        filtered_row[field] = itinerary_num
                    elif field == 'Position':
                        filtered_row[field] = pos
                    elif field == 'After a Removed Location':
                        filtered_row[field] = is_after_remove
                    else:
                        filtered_row[field] = row[field]
                is_after_remove = False
                filtered_rows.append(filtered_row)
                pos += 1
            else:
                # if there is not a higher confidence place here, we need to update the distance
                # for the next locations. Set a flag in the next location so we know to manually update.
                is_after_remove = True
        return filtered_rows    
                

def create_all_itineraries_csv(spatial_dir : str, new_filepath):
    '''Create a single csv file with names and distances for all itineraries in a directory, after filtering'''
    # Approach - create a dataframe for each file, and combine that into a dataframe used to store info from all files.
    fields = ['Itinerary','Position', 'Higher Confidence', 'Itinerary Text', 'Roman Miles', 'After a Removed Location']
    filtered_rows = []
    for filename in os.listdir(spatial_dir):
        filtered_rows += filter_itinerary(spatial_dir + '/' + filename, fields)
    with open(new_filepath, 'w') as filtered:        
        writer = csv.DictWriter(filtered, fieldnames = fields)
        writer.writeheader()
        writer.writerows(filtered_rows)
    
def get_locations_and_distances_edgebunches_from_all_itin(spatial_dir : str):
    '''Return a dictionary mapping latin names to modern names, a list of edgebunches,
    and a cost dictionary and cost list. The cost list is helpful for normalizing the costs later.'''
    
    front = "/".join(spatial_dir.split("/")[:-1])
    all_itineraries_filepath = front + '/all-itineraries-filtered.csv'
    
    # Only create the all-itineraries-filtered csv if it has not already been created.
    if 'all-itineraries-filtered.csv' not in os.listdir(front):
        create_all_itineraries_csv(spatial_dir, all_itineraries_filepath)
        print("Check for removed locations and edit the distances in a column called Modified Distances")
        return
    
    # Otherwise, use the filtered verison that has editied distances    
    # create_all_itineraries_csv(spatial_dir, all_itineraries_filepath)
    modern_to_latin = get_locations_dists_all_itin(all_itineraries_filepath)
    edgebunches = get_edgebunches_separate_itineraries(all_itineraries_filepath)
    return modern_to_latin, edgebunches

    