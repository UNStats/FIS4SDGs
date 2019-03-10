import sys
import json
import os

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

# User parameters:

property_update_only = False
update_symbology = True
update_sharing = True

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

#=======================
#'''''''''''''''''''''''
# START STAGING PROCESS
#,,,,,,,,,,,,,,,,,,,,,,,
#=======================


#=============================================
# DATA INPUTS
#=============================================

# 1. csv metadata
series_metadata = get_series_metadata(metadata_dir + 'unsd_metadata.json')

# 2. sdg_colors and icons
sdg_colors = get_series_metadata(metadata_dir + 'sdg_colors.json')

# 3. layer info template
layer_info = json.load(open(metadata_dir + 'layerinfo.json'))


#=============================================
# PUBLISHING LOOP
#=============================================

selected_series = list()
selected_series = series_metadata[:]

for s in selected_series[138:]:
    
    print("\nProcessing series code:", s["IndicatorCode"], s["SeriesCode"])
    s_color = next(item for item in sdg_colors if item['GoalCode'] == int(s['GoalCode']))
    s_card = build_series_card(s)

    if property_update_only:
        online_item = find_online_item(s_card['title'], 
                                       online_username, 
                                       gis_online_connection)

        if online_item is None:
            failed_series.append(s['SeriesCode'])
        else:
            online_item.update(item_properties=s_card, 
                               thumbnail=s_color['iconUrl'])

            if(update_symbology):
                generate_renderer_infomation(feature_item=online_item,
                                             statistic_field = 'Latest_Value',
                                             layer_info = layer_info,
                                             color=s_color['rgb'])     
    else:
        
        online_item = publish_csv(series_metadata_item = s, 
                                  item_properties=s_card,
                                  thumbnail=s_color['iconUrl'],
                                  layer_info = layer_info, 
                                  gis_online_connection= gis_online_connection,
                                  data_dir = data_dir,
                                  online_username = online_username,
                                  statistic_field = 'Latest_Value',
                                  property_update_only=False, 
                                  color=s_color["rgb"])
    
    #Only set the sharing when updating or publishing
    if online_item is not None:
        if update_sharing:
            # Share this content with the open data group
            online_item.share(everyone=False, 
                              org=True, 
                              groups=open_data_group["id"],
                              allow_members_to_edit=False)

        display(online_item)
        # Update the Group Information with Data from the Indicator and targets
        update_item_categories(online_item,
                               s["GoalCode"], 
                               s["TargetCode"],
                               gis_online_connection)

        #open_data_group.update(tags=open_data_group["tags"] + [series["code"]])
    else:
        failed_series.append(s["SeriesCode"])

        
        
