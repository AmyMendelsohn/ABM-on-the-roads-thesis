from collections import defaultdict
import random
from itineraries.create_graphs_from_csv import get_locations_and_distances_edgebunches_from_all_itin
from orbis.create_orbis_graphs import get_info_from_orbis_style_file
import mesa
import networkx as nx
from .agents import ProfitAgent, LocationAgent
from .AgentInternalDemand import InternalDemandMerchant
from .constants import *
from .reporters import *
# from mesa.space import ProductionNetworkGrid
from .Scheduler import MerchantSimultaneousActivation
import pickle, os

################################################################################
# Model
class MerchantModel(mesa.Model):
    """A model of merchant traders. 
        - num_merchants (int): the number of merchants in the model
        - num_locations (int): the number of locations in the model 
        - spatial_network_type (string)
        - social_network_type (string)
        - producer_critera (string): either 'node_degree' or 'random', determines how to choose producer  locations
        Params combined into self.experiment_params
        - distance_multiplier (float): amount to multiply distance by
        - discard_fraction (float): fraction of stock to discard
        - proportion_profit (float): fraction of agents that are profit-maximizing
        - proportion_generalist (float): fraction of agents that are generalists
        - proportion_specialist (float): fraction of agents that are specialists
        - no_trade_tolerance (int): number of timesteps without a trade until moving. Any negative number will result in no movement.
        - location_trades (bool): True if traders can trade with traders at the same location, False otherwise
        """
    def __init__(self, 
                 num_merchants, 
                 num_locations,
                 spatial_network_type=SPATIAL_NETWORK_TYPE, 
                 social_network_type=SOCIAL_NETWORK_TYPE,
                 producer_criteria=RANDOM,
                 distance_multiplier=DISTANCE_MULTIPLIER,
                 discard_fraction=DISCARD_FRACTION, 
                 proportion_profit=PROPORTION_PROFIT,
                 proportion_generalist=PROPORTION_GENERALIST,
                 proportion_specialist=PROPORTION_SPECIALIST,
                 no_trade_tolerance=NO_TRADE_TOLERANCE,
                 location_trades=LOCATION_TRADES
                 ):
        
        self.num_merchants = num_merchants
        self.num_locations = num_locations
        self.spatial_network_type = spatial_network_type
        self.social_network_type = social_network_type
        
        if proportion_profit + proportion_generalist + proportion_specialist > 1:
            raise ValueError(f"Agent type proportions add up to more than 1, with \n \
                             proportion profit: {proportion_profit}, \n \
                             proportion generalist: {proportion_generalist}, \n \
                             proportion specialist: {proportion_specialist}, \n ")
            
        self.experiment_params = {'distance_multiplier': distance_multiplier, 
                                  'discard_fraction': discard_fraction,
                                  'proportion_profit': proportion_profit,
                                  'proportion_generalist': proportion_generalist,
                                  'proportion_specialist': proportion_specialist,
                                  'no_trade_tolerance': no_trade_tolerance,
                                  'location_trades': location_trades}
        
        self.num_agents = num_merchants + num_locations
        # All location agents start with permanent_id number 500, or the nearest hundred greater than num_merchants if there are more than 499 merchants
        # If you have more merchants, then increase this number.
        if self.num_merchants > 499:
            self.first_location = (self.num_merchants // 100 + 1) * 100
        else:
            self.first_location = 500
        self.interlayer_edges = []

        self.all_modern = []

        ##################
        # Global Model Params
        # MERCURY - they tried 1, 10, 20, 30
        self.max_demand = 10

        ##################
        # Network Creation - Create networks, then create and place the agents.
        self.social_network = self.create_social_network(load_social_net=True)
        
        self.spatial_network = self.create_spatial_network()
        self.G = nx.disjoint_union(self.social_network, self.spatial_network)

        self.grid = mesa.space.NetworkGrid(self.G)
        self.schedule = MerchantSimultaneousActivation(self)
        
        # Part 2: Create and place the agents
        self.locid_to_mname = {} # dictionary to connect grid id to latin name, for use in setting production locations
        self.producer_types = self.set_producers(producer_criteria=producer_criteria)
        self.init_all_agents()
        
        self.datacollector = mesa.DataCollector(
            model_reporters = {f"{SUM_PRODUCT_REPORTER}": get_product_at_sites},
            agent_reporters = self.get_agent_reporters()
        )
        self.running = True
        self.datacollector.collect(self)



    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        
    
    ###############################
    # Helper functions

    def update_edges(self, start, old_end, new_end, color):
        ''' Update the given edges in the graph, ie remove the (start, old_end) edge
            and add the (start, new_end) edge. '''
        self.G.remove_edge(start, old_end)
        self.G.add_edge(start, new_end, color=color)

    def get_agent_by_id(self, agent_id):
        ''' Returns the agent with the given agent_id'''
        return self.schedule.agents[agent_id]
    
    def get_agent(self, id):
        '''Return the agent associated with this id'''
        agents_list = self.grid.get_cell_list_contents([id])
        return agents_list[0] if agents_list else None
    
    
    
    ### NETWORKS
    def create_new_social_net(self):
        n = self.num_merchants
        if self.social_network_type == COMPLETE_GRAPH:
            g = nx.complete_graph(n)
        elif self.social_network_type == BA_GRAPH:
            g = nx.barabasi_albert_graph(n=n, m=5)
        elif self.social_network_type == WATTS_GRAPH:
            g = nx.watts_strogatz_graph(n, k=5, p=0.5)
        else:
            raise NotImplementedError(f"The social network type {self.social_network_type} has not been implemented")
        return g
    
    def create_social_network(self, load_social_net=True):
        ''' Create a social network, or load it from a file'''
        # Attempt to open from file, if file exists:
        filename = f'social_networks/{self.spatial_network_type}_{self.social_network_type}_{self.num_merchants}.pickle'
        if load_social_net == True:
            try:
                g = pickle.load(open(filename, 'rb'))
                return g
            except:
                return self.create_new_social_net()
        else:
            return self.create_new_social_net()
        
    def create_spatial_network_from_num_locations(self):
        ''' Return a graph created with num_locations number of nodes.
        This is just for testing and to demonstrate how the model works.'''
        graph = nx.Graph()
        self.all_modern = [i for i in range(self.num_locations)]
        graph.add_nodes_from(self.all_modern)
        edges_list = [(i, i+1) for i in range(self.num_locations - 1)]
        graph.add_edges_from(edges_list, color=LOCATION_COLOR,weight=5)
        return graph

    def create_spatial_network(self):
        ''' Create the spatial network from the appropriate CSV files'''
        graph = nx.Graph()
        spatial_dir = get_spatial_dir(self.spatial_network_type)  
        
        if self.spatial_network_type == ORBIS:
            modern_to_latin, edgebunches = get_info_from_orbis_style_file(spatial_dir)
        
        elif self.spatial_network_type == ITINERARIES: 
            modern_to_latin, edgebunches = get_locations_and_distances_edgebunches_from_all_itin(spatial_dir)

        else:
            raise NotImplementedError("Spatial network type not supported")
        
        total_cost = 0
        for bunch in edgebunches:
            u, v, cost = bunch
            total_cost += cost
            # print(u,v)
            if u not in graph:
                graph.add_node(u, m_name=u, l_name=modern_to_latin[u])
            if v not in graph:
                graph.add_node(v, m_name=v, l_name=modern_to_latin[v])
        # Do not rely on these lists for order! Only for content (ie sets) or length.
        self.all_latin = list(modern_to_latin.values())
        self.all_modern = list(modern_to_latin.keys())
        graph.add_weighted_edges_from(edgebunches)
        
        # add a model attribute that has the total cost of the spatial network
        self.total_spatial_cost = total_cost
        return graph
    
    def normalize_costs(self, cost_dict, cost_list):
        '''Normalize the costs in a cost dictionary, where the the first layer has
        location1, second has location2 to cost. Cost_list has all costs.
        
        Right now the normalized costs are in the range 0 to 10...'''
        max_cost = max(cost_list)
        min_cost = min(cost_list)
        for loc2_dictionary in cost_dict.values():
            for loc2 in loc2_dictionary.keys():
                cost = loc2_dictionary[loc2]
                normalized_cost = (cost - min_cost) / (max_cost - min_cost)
                loc2_dictionary[loc2] = normalized_cost * 10
        return cost_dict
    ### AGENTS
    
    def init_all_agents(self):
        '''Initialize merchant agents, which returns a dictionary of location id to ids of merchants at the location.
        Then initialize the location agents using that dictionary.'''
        loc_to_merchants = self.init_merchant_agents()
        self.init_location_agents(loc_to_merchants)

    def init_merchant_agents(self):
        ''' Create and place all merchant agents, choosing random location ids. 
            The first ones created will be profit maximizing, then generalists, then specialists.
            Also add interlayer edges between merchants and locations.
            Return a dictionary of location id to merchant agent id at the location for use in initializing locations.'''
        filename_graph = f'social_networks/{self.spatial_network_type}_{self.social_network_type}_{self.num_merchants}.pickle'
        filename_data = f'social_networks/{self.spatial_network_type}_{self.social_network_type}_{self.num_merchants}_AGENT_INFO.pickle'
        if os.path.isfile(filename_data):
            # If the file exists, then read info from it
            data = pickle.load(open(filename_data, 'rb'))
            location_ids = data['location_ids']
            for agent_id in range(self.num_merchants):
                location_id = location_ids[agent_id]
                agent = self.create_correct_type_of_merchant(agent_id, location_id)
                self.schedule.add(agent)
                # assuming self.G was already properly loaded during the network init step
                self.grid.place_agent(agent, list(self.G)[agent_id])
            self.interlayer_edges = data['interlayer_edges']
            loc_to_merchants = data['loc_to_merchants']
            
            nx.set_node_attributes(self.social_network,
                                   data['node_attr'], 
                                   )

        else:
            # Otherwise, create the info and save to file.
            loc_to_merchants = defaultdict(list)
            location_id = self.num_merchants
            location_ids = []
            node_attr = {} 
            for agent_id in range(self.num_merchants):
                location_id = self.decide_location_id(location_id, loc_to_merchants)
                location_ids.append(location_id)
                loc_to_merchants[location_id] += [agent_id]
                
                # To go from a merchant agent... need to go from location_id to the location agent...?
                # To get the location agent, need to index at location_id - self.num_merchants
                l_name, m_name = self.get_location_name(location_id)
                node_attr[agent_id] = {'label': f'{m_name},\nagent {agent_id}',
                                       'title': f'{agent_id}',
                                       'group': f'{location_id}',
                                       'm_name': m_name,
                                       'l_name': l_name} # for updating nodes in graph
                
                agent = self.create_correct_type_of_merchant(agent_id, location_id)
                
                self.schedule.add(agent)
                self.grid.place_agent(agent, list(self.G)[agent_id])
                self.interlayer_edges.append((agent_id, location_id))
            
            nx.set_node_attributes(self.social_network,
                                   node_attr)

            ## Save to file
            data = {
                    'interlayer_edges': self.interlayer_edges,
                    'loc_to_merchants': loc_to_merchants,
                    'node_attr': node_attr,
                    'location_ids': location_ids,
                    }
            if not os.path.exists(filename_data.split('/')[0]):
                os.makedirs(filename_data.split('/')[0]) 
            pickle.dump(data, open(filename_data, 'wb'))
        
        pickle.dump(self.social_network, open(f'{filename_graph}', 'wb'))
        return loc_to_merchants

    def decide_location_id(self, start_loc, loc_to_merchants):
        ''' Decide where this merchant should be placed. Returns an integer location id.
        Uniform distribution of agents first puts on agent on each location, then 2... etc'''
        
        ## UNIFORM DISTRIBUTION OF AGENTS
        first_merchant_location = self.num_merchants
        next_loc = (start_loc + 1) % (self.num_locations + first_merchant_location)
        if next_loc == 0:
            next_loc = first_merchant_location
        return next_loc
        
        # ## RANDOM PLACEMENT OF AGENTS
        # # location_id = self.random.randrange(self.num_merchants, self.num_merchants + self.num_locations)  
        
        # return location_id
    
    
    def create_correct_type_of_merchant(self, agent_id, location_id):
        ''' Use the model_params to return the correct type of merchant object (profit, generalist, specialist)''' 
        num_profit_maxers = self.experiment_params['proportion_profit'] * self.num_merchants
        num_generalists = self.experiment_params['proportion_generalist'] * self.num_merchants
        distance_multiplier = self.experiment_params['distance_multiplier']
        
        if agent_id < num_profit_maxers:
            return ProfitAgent(agent_id, self, location_id, distance_multiplier)
        elif agent_id < num_profit_maxers + num_generalists:
            decision_strat = DecisionStrategies.GENERALIST
            return InternalDemandMerchant(agent_id, self, location_id, distance_multiplier, decision_strat)
        else:
            decision_strat = DecisionStrategies.SPECIALIST
            return InternalDemandMerchant(agent_id, self, location_id, distance_multiplier, decision_strat)
    
    def get_location_name(self, grid_id):
        '''Get the location name info based on the agent's name in the graph.
        Returns a tuple with (latin, modern).
        - `grid_id` is the agent's grid number. '''
        node_data = self.G.nodes(data=True)[grid_id]
        modern_name = node_data['m_name']
        l_name = node_data['l_name']
        return l_name, modern_name
    
    def init_location_agents(self, loc_to_merchants):
        ''' Create all location agents. First, specify which IDs should be producers.
            Then create the agent and add it appropriately to the schedule and grid. 
            Use the loc_to_merchants dictionary of locations to a list of merchants at the location.
            
            Make sure that there is only ONE location agent created per location!'''
        
        node_attr = {}
        for i in range(0, min(self.num_locations, len(self.all_modern))):
            # unique_id (grid_id) is the location in the grid
            # stable_id is the id for this agent (ie 501, 502 for locations)
            grid_id = self.num_merchants + i
            
            stable_id = self.first_location + i
            location_name = self.get_location_name(grid_id)
            l_name = location_name[0]
            m_name = location_name[1]
            
            node_attr[m_name] = {'m_name': m_name, 'label': m_name}
            
            self.locid_to_mname[grid_id] = m_name
            producer_type = self.get_producer_type(m_name)
            
            graph_neighbours = self.G[grid_id]
            neighbours = {}
            for (key, val) in graph_neighbours.items():
                if 'type' in val and val['type'] == 'spatial':
                    if 'weight' in val: 
                        neighbours[key] = val['weight']
                    else:
                        neighbours[key] = None

            location_agent = LocationAgent(grid_id, stable_id, self, producer_type, l_name, m_name, neighbours)
            location_agent.merchants = loc_to_merchants[grid_id]
            self.schedule.add(location_agent)
            self.grid.place_agent(location_agent, list(self.G)[grid_id])
        nx.set_node_attributes(self.spatial_network,
                                node_attr)
    
    def set_producers(self, producer_criteria):
        ''' Return a dictionary of location m_name to producer type'''
        if producer_criteria == NODE_DEGREE:
            producer_mnames = ['London', 'York', 'Winchester']
        elif producer_criteria == RANDOM:
            # select 3 names from random from self.all_modern
            producer_mnames = []
            producer_mnames.append(random.choice(self.all_modern))
            producer_mnames.append(random.choice(list(set(self.all_modern) - set(producer_mnames))))
            producer_mnames.append(random.choice(list(set(self.all_modern) - set(producer_mnames))))
        producer_types = {producer_mnames[0]: ProducerType.PRODUCT_A, 
                          producer_mnames[1]: ProducerType.PRODUCT_B, 
                          producer_mnames[2]: ProducerType.PRODUCT_C
                        }
        return producer_types

    def get_producer_type(self, m_name):
        ''' Return what type of producer this location agent should be, using 
        the producer_types dictionary'''
        if m_name in self.producer_types.keys():
            return self.producer_types[m_name]
        else:
            return ProducerType.NO_PRODUCT
        
    ### REPORTERS
        
    def get_agent_reporters(self):
        ''' Returns a dictionary of agent reporters for every product type currently in use'''
        reporters = {}
        reporters[f"agent_category"] = lambda a: get_agent_category(a)
        reporters[f"agent_type"] = lambda a: get_agent_type(a)
        reporters[f"agent_location"] = lambda a: get_agent_location(a)
        reporters[f"agent_stable_id"] = lambda a: get_agent_stable_id(a)
        reporters[f"latin_name"] = lambda a: get_agent_latin_name(a)
        reporters[f"modern_name"] = lambda a: get_agent_modern_name(a)
        
        for prod in Product:
            prod_type = prod.value
            if prod_type == 0:
                reporters[f"{prod.name} Product"] = lambda a: get_agent_product(0, a)
                reporters[f"{prod.name} Stock"] = lambda a: get_agent_stock(0, a)
                reporters[f"{prod.name} Demand"] = lambda a: get_agent_demand(0, a)
            elif prod_type == 1:
                reporters[f"{prod.name} Product"] = lambda a: get_agent_product(1, a)
                reporters[f"{prod.name} Stock"] = lambda a: get_agent_stock(1, a)
                reporters[f"{prod.name} Demand"] = lambda a: get_agent_demand(1, a)
            elif prod_type == 2:
                reporters[f"{prod.name} Product"] = lambda a: get_agent_product(2, a)
                reporters[f"{prod.name} Stock"] = lambda a: get_agent_stock(2, a)
                reporters[f"{prod.name} Demand"] = lambda a: get_agent_demand(2, a)
            elif prod_type == 3:
                reporters[f"{prod.name} Product"] = lambda a: get_agent_product(3, a)
                reporters[f"{prod.name} Stock"] = lambda a: get_agent_stock(3, a)
                reporters[f"{prod.name} Demand"] = lambda a: get_agent_demand(3, a)
            else:
                raise NotImplementedError("Need to add a reporter for an additional product type")
        
        reporters[f"num_trades"] = lambda a: get_agent_num_trades(a)
        reporters[f"node_degree"] = lambda a: get_node_degree(a)
        
        return reporters
