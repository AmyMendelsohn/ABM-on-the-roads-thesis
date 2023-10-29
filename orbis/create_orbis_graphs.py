from collections import defaultdict
import pandas as pd
import json
import sys
sys.path.append("..")

def get_topo_routes():
    f = open('orbis/orbis_routes_topo_o.json')
    j = json.load(f)
    topo_routes = pd.json_normalize(data=j['objects']['new_routes']['geometries'])
    return topo_routes

def create_brittania(orbis):
    '''Create a csv file with just locations in Brittania that are in the topological routes'''
    topo_routes = get_topo_routes()
    brittania = orbis[orbis['province']=='Britannia']
    all_britain_merge = brittania.merge(topo_routes, left_on='id', right_on='properties.sid')
    valid = all_britain_merge[all_britain_merge['properties.tid'].isin(brittania['id'])]
    
    brittania_costs = valid[['label', 'id_x', 'properties.tid','properties.e']]
    brittania_costs = brittania_costs.rename(columns={'label':'source', 'id_x': 'sid', 'properties.tid': 'tid', 'properties.e': 'cost'})

    id_label = orbis[['id', 'label']]
    merged = brittania_costs.merge(id_label, left_on='tid', right_on='id')
    merged = merged.rename(columns={'label': 'target'})
    merged.to_csv('./orbis_sites_brittania.csv', index=False)

    


def create_orbis_nc_simple(orbis, id_label, topo_routes):
    '''Takes in the orbis df (from orbis_sites_extended), id_label, and topological routes
    and returns a df with source, target, cost, sid, tid'''
    orbis_sourcenames_and_costs = orbis.merge(topo_routes, left_on='id', right_on='properties.sid')
    orbis_names_and_costs = orbis_sourcenames_and_costs.merge(id_label, left_on='properties.tid', right_on='id')
    orbis_nc_simple = orbis_names_and_costs[['label_x', 'label_y', 'properties.e', 'properties.sid', 'properties.tid']]
    orbis_nc_simple = orbis_nc_simple.rename(columns={'label_x':'source', 
                                                    'label_y':'target', 
                                                    'properties.e': 'cost',
                                                    'properties.sid':'sid',
                                                    'properties.tid': 'tid'})
    return orbis_nc_simple
    
def get_orbis_label_to_id():
    ''' Use the original csv of orbis sites to create a dict of id->label'''
    orbis = pd.read_csv('orbis/orbis_sites_extended.csv')
    id_label = orbis[['id', 'label']] 
    mod = id_label.set_index('label')
    dictionary = mod.to_dict()
    return list(dictionary.values())[0]

def get_orbis_id_to_label():
    ''' Use the original csv of orbis sites to create a dict of id->label'''
    orbis = pd.read_csv('orbis/orbis_sites_extended.csv')
    id_label = orbis[['id', 'label']] 
    mod = id_label.set_index('id')
    dictionary = mod.to_dict()
    return list(dictionary.values())[0]

def get_orbis_edgebunches(df, latin_to_modern):
    '''Return edgebunches. Edgebunches need to use MODERN names, to
    match the itineraries files and for consistency.'''
    bunches = []
    for _, row in df.iterrows():
        start, end, cost = (row.source, row.target, row.cost)
        start, end = latin_to_modern[start], latin_to_modern[end]
        edgebunch = (start, end, cost)
        bunches.append(edgebunch)
    return bunches

def get_info_from_orbis_style_file(file):
    '''Create locations and edgebunches from a file in the "Orbis" style,
    which means that each row has Source, Target, Cost, SID, TID. 
    
    Returns a tuple of modern to latin names, and edgebunches'''
    
    df = pd.read_csv(file)
    l_names = df['label']
    m_names = df['modern']

    modern_to_latin = defaultdict(str)
    for i, modern_name in enumerate(m_names):
        modern_to_latin[modern_name] = l_names[i]
        
    latin_to_modern = defaultdict(str)
    for i, latin_name in enumerate(l_names):
        latin_to_modern[latin_name] = m_names[i]
    
    id_label = df[['id', 'label']] 
    topo_routes = get_topo_routes()
    orbis_nc_simple = create_orbis_nc_simple(df, id_label, topo_routes)
    edgebunches = get_orbis_edgebunches(orbis_nc_simple, latin_to_modern)
    return modern_to_latin, edgebunches