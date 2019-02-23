import copy
import getpass
import json
import csv
import pandas as pd
import os
import sys
import traceback
import fnmatch
import urllib.request as request
import urllib.request as urlopen
import requests
from IPython.display import display
from arcgis.gis import GIS
# [https://developers.arcgis.com/python/](https://developers.arcgis.com/python/]

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

#--------------------------------------------
# Set path to data and metadata directories in
# the local branch 
#--------------------------------------------

data_dir = r"../../data/csv"
metadata_dir = r"../../"

# Initialize failed_series array

failed_series = []

#=============================================
# IMPORT MODULES
#=============================================



#=============================================
# INPUT USER PARAMETERS
#=============================================
        
property_update_only = False
update_symbology = True

#=============================================
# SPECIALIZED FUNCTIONS
#=============================================

#---------------------------------------------
# 

def find_online_item(title, 
                     force_find = True):
        
    try:

        # Search for this ArcGIS Online Item
        query_string = "title:'{}' AND owner:{}".format(title, online_username)
        print('Searching for ' + title)
        # The search() method returns a list of Item objects that match the 
        # search criteria
        search_results = gis_online_connection.content.search(query_string)

        if search_results:
            for search_result in search_results:
                if search_result["title"] == title:
                    return search_result
                    print ( search_result )

        # If the Item was not found in the search but it should exist use Force 
        # Find to loop all the users items (this could take a bit)
        if force_find:
            user = gis_online_connection.users.get(online_username)
            user_items = user.items(folder='Open Data', max_items=900)
            for item in user_items:
                if item["title"] == title:
                    return item
                    print(item)

        return None
    
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None
    

# -- 2. Find an existing online item for an indicator
        
def generate_renderer_infomation(feature_item, 
                                 statistic_field = "latest_value", 
                                 color = None):
    try:
        if len(color) == 3:
           color.append(130)  ###---specifies the alpha channel of the color

        #get the min/max for this item
        visual_params = layer_info["layerInfo"]
        definition_item = feature_item.layers[0]

        #get the min/max values
        out_statistics= [{"statisticType": "max",
                          "onStatisticField": "latest_value", 
                          "outStatisticFieldName": "latest_value_max"},
                        {"statisticType": "min",
                         "onStatisticField": "latest_value", 
                         "outStatisticFieldName": "latest_value_min"}]
        
        feature_set = definition_item.query(where='1=1',out_statistics=out_statistics)

        max_value = feature_set.features[0].attributes["latest_value_max"]
        min_value = feature_set.features[0].attributes["latest_value_min"]
        
        visual_params["drawingInfo"]["renderer"]["visualVariables"][0]["minDataValue"] = min_value
        visual_params["drawingInfo"]["renderer"]["visualVariables"][0]["maxDataValue"] = max_value

        visual_params["drawingInfo"]["renderer"]["authoringInfo"]["visualVariables"][0]["minSliderValue"] = min_value
        visual_params["drawingInfo"]["renderer"]["authoringInfo"]["visualVariables"][0]["maxSliderValue"] = max_value
        
        visual_params["drawingInfo"]["renderer"]["classBreakInfos"][0]["symbol"]["color"] = color
        visual_params["drawingInfo"]["renderer"]["transparency"] = 25

        definition_update_params = definition_item.properties
        definition_update_params["drawingInfo"]["renderer"] = visual_params["drawingInfo"]["renderer"]
        if "editingInfo" in definition_update_params:
            del definition_update_params["editingInfo"]
        definition_update_params["capabilities"] = "Query, Extract, Sync"
        print('Update Feature Service Symbology')
        definition_item.manager.update_definition(definition_update_params)

        return
    except:
        print("Unexpected error in generate_renderer_infomation:", sys.exc_info()[0])
        return None

#--------------------------------------------
# Connection to ArcGIS Online Organization
#--------------------------------------------

online_username = input('Username: ')
online_password = getpass.getpass('Password: ')
online_connection = "https://www.arcgis.com"
gis_online_connection = GIS(online_connection, 
                            online_username, 
                            online_password)

#--------------------------------------------
# Provide the Group ID from ArcGIS Online the 
# Data will be shared with. This should be a 
# staging group to get the data ready for 
# publishing.
#--------------------------------------------

#open_data_group_id = '967dbf64d680450eaf424ac4a38799ad'   # Travis
open_data_group_id = 'ad013d2911184063a0f0c97d252daf32'     # Luis

open_data_group = gis_online_connection.groups.get(open_data_group_id)


#--------------------------------------------
# Access to the users items may be needed to
# carry out searches and updates
#--------------------------------------------

user = gis_online_connection.users.get(online_username)
user_items = user.items(folder='Open Data', max_items=800)

#--------------------------------------------
# Cleanup staging folder for Open Data
# --> This will delete everything in the 
#     staging folder for Open Data
#--------------------------------------------

if input("Do you want to cleanup your staging folder for Open Data? (y/n)") == "y":
    if input("Are you sure? (y/n)") == "y":
        for item in user_items:
            print('deleting item ' + item.title)
            item.delete()
    else: print('Cleanup of staging forlder for Open Data was canceled') 
else:
    print('Cleanup of staging forlder for Open Data was canceled')      
    
#--------------------------------------------
# Collect Series Metadata from 
# seriesMetadata.json file
#--------------------------------------------
    
try:
    series_metadata = json.load(open(metadata_dir + "/metadata.json"))
    print("----This is an example of a series_metadata element----")
    print(series_metadata[0])
except:
    print("Unexpected error:", sys.exc_info()[0])
    
#--------------------------------------------
# Get layer info template
#--------------------------------------------

try:
    layer_info = json.load(open(metadata_dir + "/layerinfo.json"))
    print("----This is the layer info template ----")
    print(layer_info)
except:
    print("Unexpected error:", sys.exc_info()[0])
    

#-------------------------------------------------------
# Get the list of all available csv files in wide format
#-------------------------------------------------------

wide_files = []

listOfFiles = os.listdir(data_dir)  
pattern = '*_wide.csv'
for entry in listOfFiles:  
    if fnmatch.fnmatch(entry, pattern):
        wide_files.append(entry)
       
#============================================
# START PROCESSING EACH DATA SERIES
#============================================
        
# Set parameters:
        
property_update_only = False
update_symbology = True

wide_files = ['1.1.1-SI_POV_DAY1_wide.csv']
for i in range(len(wide_files)):

    #----------------------------------------
    # Read current wide file into an 
    # OrderedDict object
    #----------------------------------------
    
    f = wide_files[i]

    with open(f, encoding="utf8") as filename:
        reader = csv.reader(filename)
        data = list(reader)
        
    header = data[0]
    if(len(data)>1):
        series_df = pd.DataFrame.from_records(data[1:])
        series_df.columns = header
        
    #----------------------------------------
    # Extract series information from csv file
    #----------------------------------------
    
    series_info = series_df[['GoalCode',
                             'GoalDesc',
                             'TargetCode',
                             'TargetDesc',
                             'IndicatorCode',
                             'IndicatorDesc',
                             'SeriesCode',
                             'SeriesDesc',
                             'SeriesRelease', 
                             'Units_Code', 
                             'Units_Desc', 
                             ]].drop_duplicates().to_dict('records')
    
    if(len(series_info) > 1):
        print("The file " + f + " contains more than one series specification")
        continue
    
    series_info = series_info[0]
    
    #----------------------------------------
    # Extract matching metadata information
    #----------------------------------------
    
    for md in series_metadata:
        
        if series_info['SeriesCode'] != md['seriesCode']:
            continue
        
        # Create a dictionary containing the annotations for the current item's goal
        goal_properties = dict()
        goal_properties["title"] = "SDG " + series_info['GoalCode']
        goal_properties["description"] = series_info['GoalDesc']
        goal_properties["thumbnail"] = md["iconUrl"]

        # Create a dictionary containing the annotations for the current item's target
        target_properties = dict()
        target_properties["title"] = "Target " + series_info["TargetCode"]
        target_properties["description"] = series_info["TargetDesc"]
        
        # Create a dictionary containing the annotations for the current 
        # item's indicatorc
        indicator_properties = dict()
        indicator_properties["title"] = "Indicator " + series_info["IndicatorCode"]
        indicator_properties["snippet"] = series_info["IndicatorCode"] + ": " + series_info["IndicatorDesc"]
        indicator_properties["description"] = \
            "<p><strong>Indicator " + series_info["IndicatorCode"] + ": </strong>" + \
            series_info["IndicatorDesc"] + \
            "</p>" + \
            "<p><strong>Target " + series_info["TargetCode"] + ": </strong>" + \
            series_info["TargetDesc"] + \
            "</p>" + \
            "<p><strong>Goal " + series_info["GoalCode"] + ": </strong>" +  \
            series_info["GoalDesc"] + \
            "</p>"
        indicator_properties["credits"] = "United Nations Statistics Division"
        indicator_properties["thumbnail"] = md["iconUrl"]
        
        #----------------------------------------
        # Put together series properties for 
        # metadata card:
        #----------------------------------------
        # - title
        # - layer_title
        # - snippet
        # - description
        # - tags
        #----------------------------------------

        series_properties = dict()
        series_properties["title"] = indicator_properties["title"] + ": " + series_info["SeriesDesc"].replace('%','percent')
        series_properties["layer_title"] = series_info["SeriesDesc"].replace('%','percent').replace(",",' ').replace('/',' ')
        snippet = series_properties["title"]
        series_properties["snippet"] = (snippet[:250] + "..") if len(snippet) > 250 else snippet
        series_properties["description"] = \
            "<p><strong>Series " + series_info["SeriesCode"] + ": </strong>" + series_info["SeriesDesc"] + "</p>" + \
            indicator_properties["description"] + \
            "<p><em>Release Version: " + series_info["SeriesRelease"] + " </em>"
                                                                 
        series_tags = md["TAGS"]
        series_tags.append(series_info["SeriesRelease"])
        series_properties["tags"] = series_tags
        
        
        # Example:
        #{
        #	'title': 'Indicator 1.5.1: Number of missing persons due to disaster (number)',
        #	'layer_title': 'Number of missing persons due to disaster (number)',
        #	'snippet': 'Indicator 1.5.1: Number of missing persons due to disaster (number)',
        #	'description': '<p><strong>Series VC_DSR_MISS: </strong>Number of missing persons due to disaster (number)</p><p><strong>Indicator 1.5.1: </strong>Number of deaths, missing persons and directly affected persons attributed to disasters per 100,000 population</p><p><strong>Target 1.5: </strong>By 2030, build the resilience of the poor and those in vulnerable situations and reduce their exposure and vulnerability to climate-related extreme events and other economic, social and environmental shocks and disasters</p><p><strong>Goal 1: </strong>End poverty in all its forms everywhere</p><p><em>Release Version: 2019.Q1.G.01 </em>',
        #	'tags': ['disaster loss',
        #		'disaster prevention',
        #		'preparedness and relief',
        #		'disaster victims',
        #		'2019.Q1.G.01'
        #	]
        #}

        #================================
        # ADD ITEM TO ARCGIS ONLINE
        #================================
        
        # title:       string. The name of the new item.
        # tags:        list of string. Descriptive words that help in the searching and locating of the published information.
        # snippet:     string. A brief summary of the information being published.
        # description: string. A long description of the Item being published.
        # layers:      list of integers. If you have a layer with multiple and you only want specific layers, an index can be provided those layers. If nothing is provided, all layers will be visible.

        print("\nProcessing series code:", series_info["IndicatorCode"], series_info["SeriesCode"])
        
        #-------------------------------
        # Scenario 1: 
        # Only update information of an
        # existing layer
        #-------------------------------

        try:
            if property_update_only:
                
                online_item = find_online_item(series_properties["title"])  # See function devinition above
                if online_item is None:
                    failed_series.append(series_info["SeriesCode"])
                else:
                    # Update the Item Properties from the item_properties
                    online_item.update(item_properties=series_properties, 
                                       thumbnail=thumbnail)

                    # If Requested update the Symbology for the layer
                    if(update_symbology):
                        generate_renderer_infomation(feature_item=online_item,   # See function definition above
                                                     color=md["rgb"])
            else:
                online_item = publish_csv(series, 
                                          item_properties=series_properties,
                                          thumbnail=thumbnail,
                                          property_update_only=property_update_only, 
                                          color=series["rgb"])

            # Only set the sharing when updating or publishing
            if online_item is not None:
                if update_sharing:
                    # Share this content with the open data group
                    online_item.share(everyone=False, 
                                      org=True, 
                                      groups=open_data_group["id"],
                                      allow_members_to_edit=False)

                display(online_item)
                # Update the Group Information with Data from the Indicator and targets
                update_item_categories(online_item,series["goalCode"], 
                                       series["targetCode"])

                #open_data_group.update(tags=open_data_group["tags"] + [series["code"]])
            else:
                failed_series.append(series["seriesCode"])
        except:
            traceback.print_exc()
            print("Failed to process series code:", indicator["code"], series["code"])
            failed_series.append(series["code"])
            return



    except:
        traceback.print_exc()
