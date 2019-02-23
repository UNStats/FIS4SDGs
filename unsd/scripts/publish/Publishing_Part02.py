import sys

#--------------------------------------------
# Set up the global information and variables
#--------------------------------------------
global open_data_group         # ArcGIS group the data will be shared with
global failed_series           # Keeps track of any csv file that cannot be staged
global online_username         # ArcGIS credentials
global gis_online_connection   # ArcGIS connection
global layer_json_data         # Information pertaining to the layer template
global user_items              # Collection of items owned by user



# Initialize failed_series array
failed_series = []

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

from modules02 import *

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
