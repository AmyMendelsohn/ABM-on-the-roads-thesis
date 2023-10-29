from ABM.agents import LocationAgent, ProfitAgent, BuyOffer
from .constants import *
import random

class InternalDemandMerchant(ProfitAgent):
    """ A merchant agent that makes trade decisions based on their internal demand 
    as determined by the decision strategy
    and also has a distance_multiplier parameter"""
    def __init__(self, unique_id, model, location_id, distance_multiplier, decision_strat):
        super().__init__(unique_id, model, location_id, distance_multiplier)
        self.decision_strat = decision_strat
        if decision_strat == DecisionStrategies.SPECIALIST:
            self.specialist_item, self.specialist_index = self.choose_specialist_item()
        self.internal_demand = self.calc_internal_demand()
    
    def agent_category(self):
        return 'merchant'
    
    def short_agent_type(self):
        return 'internal demand'
        
    def choose_specialist_item(self):
        ''' if the decision strategy is specialist, then randomly choose one product
        type to be the Specialist type. '''
        
        index = self.random.choice([i for i in range(len(Product))])
        return list(Product)[index], index
        
    # There are two important parts for having different decision strategies -- 
    # 1. Creating the buy offer.
    #    - Price Maximizer : expected price based on calculation
    #    - Generalist / Specialist : Give more for a product they have less of.
    # 2. Deciding which offer to accept. 
    #    - Price Maximizer: Max Price
    #    - Generalist / Specialist: Find which types they have less of. 
    #          Accept offers of types they have less of. 
    
    def calc_internal_demand(self):
        ''' This method calculates the internal demand for each product type, based on the decision strat.
            It returns an array where each element has that distance. Positive internal demand 
            means that there is a need to buy more of this product type. '''
        # GOAL is to have equal amounts of each product type. 
        # So, each product ideally is (total product) / (# product types)
        internal_demand = []
        if self.decision_strat == DecisionStrategies.GENERALIST:
            ideal_amt = sum(self.product) / len(self.product)
            for prod_amt in list(self.product):
                dist = ideal_amt - prod_amt
                internal_demand.append(dist)
        
        elif self.decision_strat == DecisionStrategies.SPECIALIST:
            ideal_amt = 10000
            for i, prod_amt in enumerate(self.product):
                if i == self.specialist_item.value:
                    internal_demand.append(ideal_amt)
                else:
                    internal_demand.append(0)
        return internal_demand
        
    def should_make_offer(self, product_type):
        ''' Returns true if this agent needs to request a trade for this product type.
            In order to make a trade, there needs to be INTERNAL demand for this product,
            or there needs to be storage space available for the product. '''
        retval =  len(self.known_traders) > 0 \
               and (self.product[product_type] < self.internal_demand[product_type] \
               or self.max_stock_size[product_type] > 0)
        return retval
        
    def process_offers_for_product_type(self, product_type_int):
        '''Accept a trade offer if it helps you get towards distribution of goods 
           as determined by your decision strat goal, 
           not considering what demand you have left to fulfill'''
        product = self.product[product_type_int]
        product_type = list(Product)[product_type_int]
        if self.decision_strat == DecisionStrategies.SPECIALIST and product_type != self.specialist_item:
            #Specialist agents do not make trades for product types that they don't want.
            return
        # If there is no product
        if product == 0:
            if VERBOSE:
                print(f"Product {product_type_int}: No product available to sell.")
            self.move_to_stock(product_type_int)
            return

        # Go through the buy offers and see if anything is there that you want!
        if VERBOSE:
            print("Product {product_type}: There is available product to sell, checking offers...")
        
        if len(self.buy_offers[product_type_int]) > 0:
            normal_generalist = self.decision_strat == DecisionStrategies.GENERALIST and self.internal_demand[product_type_int] < 0
            normal_specialist = self.decision_strat == DecisionStrategies.SPECIALIST \
                                and self.internal_demand[product_type_int] == 0
                                # and self.internal_demand[product_type_int] <self.internal_demand[self.specialist_index]
            
            if normal_generalist:
                # if a generalist, then want to trade away any item you have TOO much of, which means ideal - amt is NEGATIVE
                highest_offer : BuyOffer = max(self.buy_offers[product_type_int], key=lambda offer: offer.price)
                self.execute_trade_away(highest_offer.unique_id, product_type_int)
            
            elif normal_specialist:
                # Specialists want to consider a buy offer for items that they want to get rid of, which means that they have no internal demand for it
                # Get the maximum-price trade offer in this agent's trade_offers list.
                highest_offer : BuyOffer = max(self.buy_offers[product_type_int], key=lambda offer: offer.price)
                self.execute_trade_away(highest_offer.unique_id, product_type_int)
        else:
            # If no agent was chosen to sell to, then reset as if no trade.
            self.move_to_stock(product_type_int)
        
    def reset(self):
        super().reset()
        self.internal_demand = self.calc_internal_demand()
        