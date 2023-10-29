import mesa
# from model import MerchantModel
import random
from ABM.constants import *
import networkx as nx

## Major differences from MERCURY model
#  - demand as a vector: it doesn't make sense to have a demand that can be filled with any type of product.
#  - max_stock_size as a vector: without this, the first product chosen is much more likely to fill up all the stock! And then the other types don't get into stock at all!
#  - trades per agent as opposed to per item: It is much more intutive to have trades be per agent. Agents are the ones who do the trading.
# 

class BuyOffer():
    ''' Buy Offers are offers from the agent with unique_id, who wants to buy one
        unit of product_type at the given price.'''
    def __init__(self, unique_id, product_type, price):
        self.unique_id = unique_id
        self.product_type = product_type
        self.price = price
    def __repr__(self):
        return (f"(Agent: {str(self.unique_id)}, "
               f"product type: {self.product_type}, "
               f"price: {self.price})")
################################################################################
##############
# Location Agents

class LocationAgent(mesa.Agent):
    """A agent that represents a trading site. 
       Args: 
            grid_id (int): a unique id representing the order agents were created.
            stable_id (int): a unique id representing this location, usually starting at 500
            model (MerchantModel): model that the site is in
            producer_type: what type of product this site produces (from the ProductionType enum)
            l_name: the location's latin name, a string
            m_name: modern name
            neighbours_dist: a dictionary of neighbor to the distance to that neighbour
    """
    def __init__(self, grid_id, stable_id, model, producer_type, l_name, m_name, neighbours):
        self.unique_id = grid_id
        self.grid_id = grid_id
        self.stable_id = stable_id
        self.model = model
        self.producer_type = producer_type
        
        self.l_name = l_name
        self.m_name = m_name
        
        self.neighbours_dist = neighbours
        
        # A list of product amounts. Index 0 has the amount for the first product type, etc.
        self.deposited_product = [0] * len(Product)
        # A list of agent_ids (ints) corresponding to agents currently at this location.
        self.merchants = []
    
    def agent_category(self):
        return 'location'
    
    def short_agent_type(self):
        return 'location'

    def __repr__(self):
        return (f"Location Agent Grid ID: {str(self.grid_id)}, "
               f"production type: {self.producer_type}, "
               f"deposited product: {self.deposited_product}, "
               f"l_name: {self.l_name}, "
               f"m_name: {self.m_name}, "
               f"neighbours: {self.neighbours_dist}")
        
    def set_deposited_product(self, product_type, amount):
        '''Update the amount of deposited_product to be the given amount'''
        self.deposited_product[product_type] = amount
        
    def remove_from_merchants(self, agent_id):
        self.merchants.remove(agent_id)
    
    def add_to_merchants(self, agent_id):
        self.merchants.append(agent_id)
        
    def get_node_degree(self):
        return len(self.neighbours_dist)

    def step(self):
        pass
    def update_price(self):
        pass
    def advance(self):
        pass

    def reset(self):
        pass
    def determine_demand(self):
        pass
    def discard_part_of_stock(self):
        pass
    def get_newly_produced_product(self):
        pass
    def update_price_and_max_s_s(self):
        pass
    def make_buy_offers(self):
        pass
    def process_offers(self):
        pass
    def move(self):
        pass



################################################################################
##############
# Merchant Agents

class ProfitAgent(mesa.Agent):
    """ A base merchant agent that uses profit-maximization.

        Args:
            unique_id (int): A unique numeric identifier for the agent
            model (Model): Instance of the model that contains the agent
            location_id (int): Identifier for the location that the agent is at
            distance_multiplier (float): a float from 0 - 1 that the distance is multiplied by
    """
    def __init__(self, unique_id, model, location_id, distance_multiplier):
        super().__init__(unique_id, model)
        self.unique_id = unique_id
        self.model = model
        self.location_id = location_id
        self.distance_multiplier = distance_multiplier
        
        # Initialized in the `reset` method
        self.known_traders = []
        
        self.product = [0 for prod in Product]
        # stock vector
        self.stock = [0] * len(self.product)
        # max_stock_size vector, with values initialized later
        self.max_stock_size = [None] * len(self.product) 
        # from the MERCURY model: all demand is initialized as 0
        self.demand = [0] * len(self.product)
        # A list of lists, where each inner list is a list of offers for one prod type
        self.buy_offers = [[] for _ in range(len(list(Product)))]
        # Counter for the number of successfully executed trades
        self.num_trades = 0
        # Counter for number of timesteps since a successful trade
        self.time_since_trade = 0
        
    def agent_category(self):
        return 'merchant'

    def short_agent_type(self):
        return 'base'
    
    def __repr__(self):
        return (f"Agent {str(self.unique_id)}, " 
                f"Location_id: {self.location_id}, " 
                f"Product: {self.product}, " 
                f"Stock: {self.stock}, " 
                f"Demand: {self.demand}, "
                f"Max Stock Size: {self.max_stock_size}")
        
    def get_node_degree(self):
        return len(self.known_traders)

    ################################################################################
    ### Getters, Setters, and other "initialization" methods
    def get_location_id(self):
        return self.location_id
    def get_location_mname(self):
        return self.model.locid_to_mname[self.location_id]
    def get_location_agent(self) -> LocationAgent:
        '''Returns the location agent associated with the location id'''
        return self.model.get_agent(self.location_id)

    def get_known_traders(self):
        '''Returns MerchantAgent neighbor nodes.'''
        neighbors = self.model.social_network.neighbors(self.unique_id)
        # gets unique ids of neighbor nodes
        ids = [n for n in neighbors]
        # get nodes from unique ids using grid
        nodes = self.model.grid.get_cell_list_contents(ids)
        return nodes
    
    def get_product(self, product_type):
        return self.product[product_type]

    def set_product(self, product_type, amt):
        '''Update product vector to have product_type with the new amount'''
        self.product[product_type] = amt

    def set_stock(self, product_type, amt):
        ''' Update stock vector for this product_type to have given amt'''
        self.stock[product_type] = amt

    def set_max_stock_size(self, product_type, amt):
        ''' Set max_stock_size to amt. Note that max_stock_size can be negative.
            Max stock size is a vector, with each value corresponding to a product type'''
        self.max_stock_size[product_type] = amt

    def subtract_from_max_stock_size(self, product_type, amt):
        ''' Subtract amt from the max_stock_size for this product type '''
        self.max_stock_size[product_type] = self.max_stock_size[product_type] - amt

    def deposit_to_location(self, product_type, amt):
        ''' Deposit amt of product_type to current location'''
        location_agent : LocationAgent = self.get_location_agent()
        new_product = location_agent.deposited_product[product_type] + amt
        location_agent.set_deposited_product(product_type, new_product)

    def calc_expected_price(self):
        '''Use average supply and demand info to determine your expected price.'''
        avg_supply = self.get_average_supply()
        avg_demand = self.get_average_demand()
        return avg_demand / (avg_supply + avg_demand) if avg_supply + avg_demand != 0 else avg_demand/0.00001

    def get_average_supply(self):
        '''Get average supply of traders (including yourself)'''
        product_vectors = [a.product for a in self.known_traders]
        stock_vectors = [a.stock for a in self.known_traders]
        supply_vectors = product_vectors + stock_vectors
        supplies = [sum(items) for items in supply_vectors]
        return (sum(supplies) + sum(self.product)) / (len(self.known_traders) + 1)

    def get_average_demand(self):
        '''Get average demand of traders '''
        demand_vectors = [a.demand for a in self.known_traders]
        demands = [sum(demand) for demand in demand_vectors]
        return sum(demands) / len(self.known_traders) if len(self.known_traders) > 0 else 0


    ################################################################################
    ### Action methods

    ##### Demand
    def determine_demand(self):
        '''Update demand for all product types'''
        for prod in Product:
            self.update_demand_single(prod.value)
        if VERBOSE:
            print(f"Agent {self.unique_id}: {self.demand}")

    def update_demand_single(self, product_type):
        ''' At each timestep, demand increases by 1 if demand is lower than max_demand'''
        if self.demand[product_type] < self.model.max_demand:
            self.demand[product_type] += 1

    ##### Discard part of stock
    def discard_part_of_stock(self):
        ''' Discard stock for each product type'''
        for prod in Product:
            self.discard_stock_for_product_type(prod.value)
        if VERBOSE:
            print(f"Agent {self.unique_id}, product: {self.product}, stock: {self.stock}, demand: {self.demand}")

    def discard_stock_for_product_type(self, product_type):
        ''' DISCARD_FRACTION of stock from previous timestep is deposited onto location agent, 
            and the rest is moved to product '''
        
        amount_to_deposit = round(self.model.experiment_params['discard_fraction'] * self.stock[product_type])
        if DEBUGGING_VERBOSE:
            print(f"amount to deposit: {amount_to_deposit}")
        self.demand[product_type] = max(self.demand[product_type] - amount_to_deposit, 0)

        self.deposit_to_location(product_type, amount_to_deposit)

        # Move rest to product
        current_product = self.product[product_type]
        current_stock = self.stock[product_type]
        self.set_product(product_type, current_product + current_stock - amount_to_deposit)
        self.set_stock(product_type, 0)
    
    ##### Produce some product
    def get_newly_produced_product(self):
        '''Traders at production sites obtain new items at each timestep, if 
           they currently have some unmet demand for the product type that this
           location produces. Their demand for this product is fully met.'''
        location_agent : LocationAgent = self.get_location_agent()
        if location_agent.producer_type != ProducerType.NO_PRODUCT:
            for prod in Product:
                if prod == location_agent.producer_type.value:
                    product_type = prod.value

                    # Calculate if they have unmet demand
                    unmet_demand = self.demand[product_type] - (self.product[product_type] + self.stock[product_type])
                    if unmet_demand > 0:
                        # then they need to have their demand met (via product)
                        self.set_product(product_type, self.product[product_type] + unmet_demand)
        if VERBOSE:
            print(f"Agent {self.unique_id}, product: {self.product}")

    ##### Update price and max stock size
    def update_price_and_max_s_s(self):
        self.update_max_stock_size()
        self.update_price()
        if VERBOSE:
            print(f"Agent: {self.unique_id}, max_s_s: {self.max_stock_size}, price: {self.expected_price}")

    def update_max_stock_size(self):
        '''Update the max_stock_size attribute.
        Every trader has a max_stock_size, which is the average demand of other
        known traders minus their own demand, rounded. 
        This is higher than 0 when avg demand is higher than the trader's own demand,
        meaning the trader thinks there's a reason to have stock.'''
        for prod in Product:
            product_type = prod.value 
            self.update_max_stock_size_for_product_type(product_type)
           
    def update_max_stock_size_for_product_type(self, product_type):
        ''' Update max_stock_size for this product type'''
        avg_demand = self.get_average_demand()
        self.set_max_stock_size(product_type, round(avg_demand - sum(self.demand)))

    def update_price(self):
        ''' Initialize the expected price attribute of this agent. This needs to 
            be done before it is used when considering BuyOffers in advance()'''
        self.expected_price = self.calc_expected_price()


    ##### Offers    
    def make_buy_offers(self):
        ''' For each product type, determine if there should be a buy offer made.
            Make the offer if so.''' 
        for prod in Product:
            product_type = prod.value 
            
            if self.should_make_offer(product_type):
                self.make_offer(product_type)
            else: 
                # If not making a buy offer, still don't know if you will be selling
                # one unit of this product type or not, so you can't do anything
                # else at this point.
                pass 

    def should_make_offer(self, product_type):
        ''' Returns true if this agent needs to request a trade for this product type.
            In order to make a trade, there needs to be demand for this product,
            or there needs to be storage space available for the product. '''
        retval = len(self.known_traders) > 0 \
               and (self.product[product_type] < self.demand[product_type] \
               or self.max_stock_size[product_type] > 0)
        return retval
    
    def make_offer(self, product_type):
        ''' Requesting a trade means adding yourself to the Seller's trade_offers list.'''
        if VERBOSE:
            print(f"Agent {self.unique_id} is requesting a trade")
        
        potential_traders_ids = [a.unique_id for a in self.known_traders]
        if self.model.experiment_params['location_trades']:
            location_agent : LocationAgent = self.get_location_agent()
            merchants = location_agent.merchants
            potential_traders_ids.extend(merchants)
            
        potential_seller_id = self.random.choice(potential_traders_ids)
        potential_seller : ProfitAgent = self.model.get_agent(potential_seller_id)
        offer_price = self.get_buy_offer_price(potential_seller)
        offer = BuyOffer(self.unique_id, product_type, offer_price)

        potential_seller.buy_offers[product_type] += [offer]
        if VERBOSE:
            print(f"Offer of {offer} made to Agent {potential_seller.unique_id}")

    def get_buy_offer_price(self, potential_seller):
        ''' Return the price that will be passed into the buy offer.
            This method will be overloaded in other agent types'''
        source_loc_agent :LocationAgent = self.get_location_agent()
        target_loc_agent = potential_seller.get_location_agent()
        source_name = source_loc_agent.m_name
        target_name = target_loc_agent.m_name
        try:
            shortest_path_len = nx.shortest_path_length(self.model.spatial_network,
                                            source=source_name,
                                            target=target_name, 
                                            weight='weight')
            # Transport cost needs to be between 0 and 1. 
            # It is  the proportion that this distance is (multiplied by
            # the multiplier) out of the total spatial network.
            transport_cost = (self.distance_multiplier * shortest_path_len) / self.model.total_spatial_cost
            return self.expected_price - transport_cost
        except:
            return 0
        
    ###### Process offers 
    def process_offers(self):
        ''' Consider all trade offers for each product type. '''
        if VERBOSE:
            print(f"Agent {self.unique_id}, offers: {self.buy_offers}")
        for prod in Product:
            product_type = prod.value 
            self.process_offers_for_product_type(product_type)
    

    def process_offers_for_product_type(self, product_type):
        '''Accept a trade offer if the price offered is higher than your expected price'''
        trade_executed_flag = False
        product = self.product[product_type]
        demand = self.demand[product_type]

        # If there is no product available to sell
        if product < demand or product == 0:
            if VERBOSE:
                print(f"Product {product_type}: No product available to sell.")
            self.move_to_stock(product_type)
            return

        # Find the highest trade offer in self.trade_offers
        if VERBOSE:
            print("Product {product_type}: There is available product to sell, checking offers...")
        if self.buy_offers[product_type]:
            # Get the maximum-price trade offer in this agent's trade_offers list.
            highest_offer : BuyOffer = max(self.buy_offers[product_type], key=lambda offer: offer.price)
            # Check if offer price is larger than the expected price
            offer_price = highest_offer.price
            if VERBOSE:
                print(f"offer price: {offer_price}, expected price: {self.expected_price}")
            if offer_price > self.expected_price:
                # Execute the trade.
                trade_executed_flag = True
                self.execute_trade_away(highest_offer.unique_id, product_type)
            
        if not trade_executed_flag:
            # If no agent was chosen to sell to, then reset as if no trade.
            self.move_to_stock(product_type)

    def move_to_stock(self, product_type):
        ''' Do what must be done if no trade will occur for this product type for this agent.
        This means moving all items of this type to stock, and decrementing max_stock_size
        as appropriate. Also, increment the time_since_trade variable'''
        self.set_stock(product_type, self.product[product_type])
        self.subtract_from_max_stock_size(product_type, self.product[product_type])
        self.set_product(product_type, 0)
        self.time_since_trade += 1

    
    def execute_trade_away(self, buyer_id, product_type):
        ''' Trade one unit of product from this agent to the other agent'''
        if VERBOSE:
            print("Trade accepted.")
        self.set_product(product_type, self.product[product_type] - 1)
        
        # The buyer must decide whether to put item in stock or sell to consumer immediately.
        buyer : ProfitAgent = self.model.grid.get_cell_list_contents([buyer_id])[0]
        
        if buyer.demand[product_type] > 0:
            if VERBOSE:
                print("Buyer placing item into stock.")
            buyer.set_stock(product_type, buyer.stock[product_type] + 1)
            buyer.subtract_from_max_stock_size(product_type, 1)
            if DEBUGGING_VERBOSE:
                print(f"Buyer stock, mss: {buyer.stock}, {buyer.max_stock_size}")
        else: 
            if VERBOSE:
                print("Buyer depositing to location.")
            buyer.deposit_to_location(product_type, 1)
        
        self.num_trades += 1
        buyer.num_trades += 1
        self.time_since_trade = 0

    ####### 
    # Movement
    
    def move(self):
        '''Decide whether to move to another location, and if so, then move. 
           Negative values of no_trade_tolerance result in no movement'''
        
        no_trade_tolerance = self.model.experiment_params['no_trade_tolerance']
        
        if no_trade_tolerance >= 0 and self.time_since_trade >= no_trade_tolerance:
            # If the time limit is reached, then there is some percent chance of moving.
            coin = random.random()
            if coin > 0.8:
                self.move_to_neighbour()

    def move_to_neighbour(self):
        '''Move this agent to a randomly-chosen neighbour.'''
        old_location_agent : LocationAgent = self.get_location_agent()
        neighbours = old_location_agent.neighbours_dist
        
        # Choose  neighbour in the dictionary
        new_location_id, dist = random.choice(list(neighbours.items()))
        
        # Update intralayer edges
        self.model.update_edges(self.unique_id, self.location_id, new_location_id, color=INTERLAYER_COLOR)
                
        # Update location id
        self.location_id = new_location_id
        
        # Update locations
        old_location_agent.remove_from_merchants(self.unique_id)
        new_location_agent : LocationAgent = self.get_location_agent()
        new_location_agent.add_to_merchants(self.unique_id)
        
        
    
    def reset(self):
        '''Reset variables related to each step'''
        self.known_traders = self.get_known_traders()
        self.buy_offers = [[] for _ in range(len(list(Product)))]
