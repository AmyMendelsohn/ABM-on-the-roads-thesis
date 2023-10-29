from ABM.model import LocationAgent, ProfitAgent, ProducerType
#########################
## Reporters
## 
## This file has reporters that are not part of the Model class, but are used
## in reporting model and agent statuses
#########################


## Model reporters

def compute_avg_supply_demand_ratio(model):
    supply_demand_ratio = [sum(a.product)/(sum(a.demand)+1) for a in model.schedule.agents]
    avg = sum(supply_demand_ratio) / len(supply_demand_ratio)
    return avg

def get_product_at_sites(model):
    ''' Return the amount of product at all sites'''
    total = 0
    for node in model.schedule.agents:
        if type(node) is LocationAgent:
            total += sum(node.deposited_product)
    return total

def get_avg_num_known_traders(model):
    total = 0
    count = 0
    for node in model.schedule.agents:
        if type(node) is not LocationAgent:
            total += len(node.known_traders)
            count += 1
    return total / count
        
## Agent reporters

def get_agent_location(a):
    if type(a) is LocationAgent:
        return a.m_name
    elif type(a) is ProfitAgent or issubclass(type(a), ProfitAgent):
        return a.get_location_mname()

def get_agent_product(product_type, a):
    ''' Return the agent's product or deposited_product of the given product_type'''
    if type(a) is LocationAgent:
        return a.deposited_product[product_type]
    elif type(a) is ProfitAgent or issubclass(type(a), ProfitAgent):
        return a.get_product(product_type)
    else:
        raise NotImplementedError("check profit for other agents")

def get_agent_stock(product_type, a):
    ''' Return the agent's product or deposited_product of the given product_type'''
    if type(a) is LocationAgent:
        return "NA"
    else:
        return a.stock[product_type]

def get_agent_demand(product_type, a):
    ''' Return the agent's product or deposited_product of the given product_type'''
    if type(a) is LocationAgent:
        return "NA"
    else:
        return a.demand[product_type]
    
def get_agent_num_trades(a):
    if type(a) is LocationAgent:
        return "NA"
    else:
        return a.num_trades
    
def get_agent_category(a):
    return a.agent_category()
    
def get_agent_type(a):
    return a.short_agent_type()
    
def get_agent_stable_id(a):
    if type(a) is LocationAgent:
        return a.stable_id
    else:
        return a.unique_id
    
def get_agent_latin_name(a):
    if type(a) is LocationAgent:
        if a.producer_type != ProducerType.NO_PRODUCT:
            return f'{a.producer_type} {a.l_name}'
        return a.l_name
    else:
        return "merchant agent"
    
def get_agent_modern_name(a):
    if type(a) is LocationAgent:
        if a.producer_type != ProducerType.NO_PRODUCT:
            return f'{a.producer_type} {a.m_name}'
        return a.m_name
    else:
        return "merchant agent"

def get_node_degree(a):
    return a.get_node_degree()