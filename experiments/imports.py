import matplotlib.pyplot as plt, seaborn as sns
import os
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings('ignore', ".*The palette list.*")


# Folder name where output files should be stored
output_path = './outputs'