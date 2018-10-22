# -*- coding: utf-8 -*-
"""
Created on Sat Jun 30 09:58:01 2018
This script will allow the user to input a card of data and update to meet to specifications of the UNSD Metadata cards=
@author: UNSD
"""

# -----------------------
# Import python libraries
# -----------------------

# https://docs.python.org/3/library/copy.html
# Shallow and deep copy operations
import copy

# https://docs.python.org/3/library/getpass.html
# Portable password input
# Used to prompt for user input. When using this script internally, you may
# remove this and simply hard code in your username and password
import getpass

# https://docs.python.org/3/library/json.html
# JSON encoder and decoder
import json

# https://docs.python.org/3/library/os.html
# Miscellaneous operating system interfaces
import os

# https://docs.python.org/3/library/re.html
# Regular expression operations
# import re

# https://docs.python.org/3/library/sys.html
# System-specific parameters and functions
import sys

# https://docs.python.org/3/library/time.html
# Time access and conversions
# import time

# https://docs.python.org/3/library/traceback.html
# Print or retrieve a stack traceback
import traceback

# https://docs.python.org/3/library/urllib.html
# URL handling modules
# import urllib

# https://docs.python.org/3/library/urllib.request.html
# Extensible library for opening URLs
import urllib.request as request

# https://docs.python.org/3/library/urllib.request.html
# Extensible library for opening URLs
import urllib.request as urlopen

# https://docs.python.org/3/library/datetime.html#datetime-objects
# A datetime object is a single object containing all the information from a
# date object and a time object
# from datetime import datetime

# http://docs.python-requests.org/en/master/
# HTTP for Humans
import requests

# http://ipython.readthedocs.io/en/stable/api/generated/IPython.display.html
# Public API for display tools in IPython.
# Optional component to help debug within the Python Notebook
from IPython.display import display

# https://developers.arcgis.com/python/guide/using-the-gis/
# ArcGIS API for Python.
# The GIS object represents the GIS you are working with, be it ArcGIS Online
# or an instance of ArcGIS Enterprise.
# Use the GIS object to consume and publish GIS content, and to manage GIS
# users, groups and datastore
from arcgis.gis import GIS

###############################################################################

def main():
    
    # Set up the global information and variables
    global data_dir                # Directory where csv files are located
    global metadata_dir            # Directory where meatadata files are located
    global open_data_group         # ArcGIS group the data will be shared with
    global failed_series
    global online_username
    global gis_online_connection
    global layer_json_data
    global user_items

    failed_series = []
    
    # ### Create a connection to your ArcGIS Online Organization
    # Use the ArcGIS API for python to connect to your ArcGIS Online Organization 
    # to publish and manage data.  For more information about this python library
    # visit the developer resources at 
    # [https://developers.arcgis.com/python/](https://developers.arcgis.com/python/]
    online_username = input('Username: ')
    online_password = getpass.getpass('Password: ')
    online_connection = "https://www.arcgis.com"
    gis_online_connection = GIS(online_connection, 
                                online_username, 
                                online_password)

    
    # Get data and metadata from the local branch ("r" prefix means "raw string 
    # literal"). 
    data_dir = r"../../data/csv"
    metadata_dir = r"../../"
    
    
    # Access to the users items may be needed in order to 
    # carry out searches and updates
    user = gis_online_connection.users.get(online_username)

    #Find the Item you are looking to update (this section could be scripted to input many items)
    update_card_information('41f1252fa7ab435e8bb812523200a8b0','1.1.1')

    return

###############################################################################
# ### Find an existing online item for an indicator
def find_online_item(title,
                     force_find=True):
        
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
                    #return search_result
                    print ( search_result )


        # If the Item was not found in the search but it should exist use Force 
        # Find to loop all the users items (this could take a bit)
        if force_find:
            user = gis_online_connection.users.get(online_username)
            user_items = user.items(folder='Open Data', max_items=800)
            for item in user_items:
                if item["title"] == title:
                    print(item)
                    return item

        return None
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None
    

def generate_renderer_infomation(feature_item, 
                                 statistic_field="latest_value", 
                                 color=None):
    try:
        if len(color) == 3:
            color.append(130)  ###---specifies the alpha channel of the color

        layer_json_data = get_layer_template()
        
        #get the min/max for this item
        visual_params = layer_json_data["layerInfo"]
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

def update_card_information(item_id, indicator_code=None):
    try:
        series_metadata = get_seriesMetadata()
        print(series_metadata[0])

        for series in series_metadata:
            
            ### series = series_metadata[0]
            
            # Find the Correct indicator in the series metadata
            if indicator_code is not None and series["indicatorCode"] not in indicator_code:
                continue
            
            thumbnail = series["iconUrl"]
            
            # Create a dictionary containing the annotations for the current item's goal
            goal_properties = dict()
            goal_properties["title"] = "SDG " + str(series["goalCode"])
            goal_properties["description"] = series["goalDescription"]
            goal_properties["thumbnail"] = thumbnail

            # Create a dictionary containing the annotations for the current item's target
            target_properties = dict()
            target_properties["title"] = "Target " + series["targetCode"]
            target_properties["description"] = series["targetDescription"]
            
            # Create a dictionary containing the annotations for the current 
            # item's indicatorc
            indicator_properties = dict()
            indicator_properties["title"] = "Indicator " + series["indicatorCode"]
            indicator_properties["snippet"] = series["indicatorCode"] + ": " + series["indicatorDescription"]
            indicator_properties["description"] = \
                "<p><strong>Indicator " + series["indicatorCode"] + ": </strong>" + \
                series["indicatorDescription"] + \
                "</p>" + \
                "<p><strong>Target " + series["targetCode"] + ": </strong>" + \
                series["targetDescription"] + \
                "</p>" + \
                "<p><strong>Goal " + str(series["goalCode"]) + ": </strong>" +  \
                series["goalDescription"] + \
                "</p>"
            indicator_properties["credits"] = "United Nations Statistics Division"
            indicator_properties["thumbnail"] = thumbnail
            indicator_properties["tags"] = series["TAGS"]

            # ------------------------------
            # Update the Item Card in ArcGIS Online
            # ------------------------------
#            title:	      string. The name of the new item.
#            tags:        list of string. Descriptive words that help in the searching and locating of the published information.
#            snippet:     string. A brief summary of the information being published.
#            description: string. A long description of the Item being published.
#            layers:      list of integers. If you have a layer with multiple and you only want specific layers, an index can be provided those layers. If nothing is provided, all layers will be visible.
            print("\nProcessing series code:", series["indicatorCode"])
            #### property_update_only = False
            try:

                online_item = gis_online_connection.content.get(item_id) #  find_online_item(series_properties["title"])
                if online_item is None:
                    failed_series.append(series["code"])
                else:
                    # Update the Item Properties from the item_properties
                    online_item.update(item_properties=indicator_properties, 
                                        thumbnail=thumbnail)

            except:
                traceback.print_exc()
                print("Failed to process")
                return



    except:
        traceback.print_exc()


# ### Collect Series Metadata
# Return all the metadata contained in the seriesMetadata.json file
def get_seriesMetadata():
    try:
        seriesMetadata_json_data = json.load(open(metadata_dir + "/metadata.json"))
        return seriesMetadata_json_data
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None

#set the primary starting point
if __name__ == "__main__":
    main()      

