import sys
import json

#--------------------------------------------
# Set up the global information and variables
#--------------------------------------------

global data_dir                # Directory where csv files are located
global metadata_dir            # Directory where meatadata files are located

#=============================================
# INPUT USER PARAMETERS
#=============================================
property_update_only = False
update_symbology = True

#--------------------------------------------
# Set path to data and metadata directories in
# the local branch 
#--------------------------------------------

data_dir = r"../../data/csv/"
metadata_dir = r"../../"
modules_dir = r"../modules/"

#=============================================
# IMPORT MODULES
#=============================================

sys.path.append(modules_dir)
# sys.path

from modules01 import *


#=============================================
# GET METADATA
#=============================================

series_metadata = get_series_metadata(metadata_dir + "metadata.json")

wide_files = get_file_catalog(data_dir, pattern = 'country_*_wide.csv')

key_list = ['GoalCode', 'GoalDesc',
            'TargetCode', 'TargetDesc', 
            'IndicatorCode', 'IndicatorDesc', 'IndicatorTier', 
            'SeriesCode', 'SeriesDesc', 'SeriesRelease']

csv_metadata = get_csv_metadata(wide_files, key_list, data_dir)

#----------------------------------------------

# Extract logos and color schemes for each goal
sdg_colors = get_sdg_colors(series_metadata)
with open(metadata_dir + 'sdg_colors.json', 'w') as fp:
    json.dump(sdg_colors, fp, indent=2)

#----------------------------------------------

# Add tags to csv metadata (from current metadata.json file)
csv_metadata = add_tags_to_csv_metadata(csv_metadata, series_metadata)

with open(metadata_dir + 'unsd_metadata.json', 'w') as fp:
    json.dump(csv_metadata, fp, indent=2)
        




