from mesa.time import BaseScheduler
from .constants import VERBOSE
import random
import numpy as np

class MerchantSimultaneousActivation(BaseScheduler):
    """A scheduler to simulate the activation of the merchant agents.

    This scheduler requires that each agent have 

    """

    def step(self) -> None:
        """Step all agents"""
        # What must be done for each agent:
        # self.reset()
        # self.determine_demand()
        # self.discard_part_of_stock()
        # self.get_newly_produced_product()
        # self.update_max_stock_size()
        # self.make_buy_offers()
        # self.process_offers()
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].reset()
        
        if VERBOSE:
            print(f"\n\n\n Step {self.steps}")
            print("****** \nDemand (after update)")
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].determine_demand()
        
        if VERBOSE:
            print("\n****** \nDiscard stock")
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].discard_part_of_stock()

        if VERBOSE:
            print("\n****** \nProduct (amount of product after production)")
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].get_newly_produced_product()


        if VERBOSE:
            print("\n****** \nAfter updating max_s_s and price: ")        
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].update_price_and_max_s_s()

        
        if VERBOSE:
            print("\n****** Making buy offers")
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].make_buy_offers()


        if VERBOSE:
            print("\n****** Processing buy offers")        
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].process_offers()

        if VERBOSE:
            print("\n****** Potentially moving locations")        
        for agent_key in self.random_order_agent_keys():
            self._agents[agent_key].move()
            
        self.steps += 1
        self.time += 1
        
    def random_order_agent_keys(self):
        keys = list(self._agents.keys())
        random.shuffle(list(self._agents.keys()))
        return keys