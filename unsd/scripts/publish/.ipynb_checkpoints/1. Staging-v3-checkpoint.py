import sys

#--------------------------------------------
# Set up the global information and variables
#--------------------------------------------

global data_dir                # Directory where csv files are located
global metadata_dir            # Directory where meatadata files are located
global open_data_group         # ArcGIS group the data will be shared with
global failed_series           # Keeps track of any csv file that cannot be staged
global online_username         # ArcGIS credentials
global gis_online_connection   # ArcGIS connection
global layer_json_data         # Information pertaining to the layer template
global user_items              # Collection of items owned by user


# Initialize failed_series array
failed_series = []

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
# ESTABLISH CONNECTIONS TO ARCGIS
#=============================================

#--- Get ArcGIS connection:
online_username, gis_online_connection = connect_to_arcGIS()

#--- Get open data group:
open_data_group = open_data_group(gis_online_connection,'ad013d2911184063a0f0c97d252daf32' ) # Luis
#open_data_group = open_data_group(gis_online_connection,'967dbf64d680450eaf424ac4a38799ad' ) # Travis

#--- Access to the user's items may be needed to carry out searches and updates:
user = gis_online_connection.users.get(online_username)
user_items = user.items(folder='Open Data', max_items=800)

#=============================================
# CLEANUP
#=============================================

cleanup_staging_folder(user_items)

#=============================================
# GET METADATA
#=============================================

series_metadata = get_series_metadata(metadata_dir + "metadata.json")

layer_info = get_layer_info_template(metadata_dir + "layerinfo.json")

wide_files = get_file_catalog(data_dir, pattern = '*_wide.csv')

key_list = ['GoalCode', 'GoalDesc',
            'TargetCode', 'TargetDesc', 
            'IndicatorCode', 'IndicatorDesc', 'IndicatorTier', 
            'SeriesCode', 'SeriesDesc', 'SeriesRelease']

csv_metadta = get_csv_metadata(wide_files, key_list, data_dir)

#----------------------------------------------

# Extract logos and color schemes for each goal
sdg_colors = get_sdg_colors(series_metadata)

#----------------------------------------------





