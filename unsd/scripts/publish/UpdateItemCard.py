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
    global failed_series
    global online_username
    global gis_online_connection

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

    #Find the Item you are looking to update (this section could be scripted to input many items)
    update_card_information('41f1252fa7ab435e8bb812523200a8b0','1.1.1')
    return

###############################################################################
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

