from enum import Enum
import os

# Configuration option: Mac / Windows
MAC = True

## Spatial Networks
ORBIS_NUM_LOCATIONS = 24
ITER_NUM_LOCATIONS = 94
ORBIS = 'orbis'
ITINERARIES = 'itineraries'

# Data filepaths
module_path = os.path.dirname(os.path.realpath(__file__))
all_itineraries_dir = os.path.join(module_path, '../itineraries/itineraries-files')
orbis_britain_file = os.path.join(module_path, '../orbis/orbis_sites_brittania.csv')

def get_num_locations(spatial_network_type):
    return ORBIS_NUM_LOCATIONS if spatial_network_type==ORBIS else ITER_NUM_LOCATIONS

def get_spatial_dir(spatial_network_type):
    return orbis_britain_file if spatial_network_type == ORBIS else all_itineraries_dir

## Social Networks
COMPLETE_GRAPH = 'complete'
BA_GRAPH = 'ba'
WATTS_GRAPH = 'watts-strogatz'

## Producer criteria
NODE_DEGREE = "node degree"
RANDOM = "random"

## Basic Parameters
# The following will be overwritten by batch-run parameters, but are provided
# for use in manual testing only
NUM_MERCHANTS          = 10 
SPATIAL_NETWORK_TYPE   = ORBIS
SOCIAL_NETWORK_TYPE    = 'test'
NUM_LOCATIONS          = get_num_locations(SPATIAL_NETWORK_TYPE)
DISTANCE_MULTIPLIER    = 0.3
DISCARD_FRACTION       = 0.14 # Mercury = 0.14
PROPORTION_PROFIT      = 1
PROPORTION_GENERALIST  = 0
PROPORTION_SPECIALIST  = 0
NO_TRADE_TOLERANCE     = -1
LOCATION_TRADES        = False

## Types

PRODUCTS = ["PRODUCT_A Product", "PRODUCT_B Product", "PRODUCT_C Product"]


# Product lists assume product types are 0 indexed and increment by 1
class Product(Enum):
    PRODUCT_A = 0
    PRODUCT_B = 1
    PRODUCT_C = 2

class ProducerType(Enum):
    NO_PRODUCT = -100
    PRODUCT_A = Product.PRODUCT_A
    PRODUCT_B = Product.PRODUCT_B
    PRODUCT_C = Product.PRODUCT_C

class DecisionStrategies(Enum):
    GENERALIST = 0
    SPECIALIST = 1

# Reporters
SUM_PRODUCT_REPORTER = "sum_product_all_sites"

### Configuration options for testing model
# Verbose options and Mac/Windows
VERBOSE = False
DEBUGGING_VERBOSE = False

# Colors for visualizations
RED = "#CC0000" # red
MERCHANT_COLOR = "#007959"
LOCATION_COLOR = "#00CCCC" # Teal
INTERLAYER_COLOR = 'red'