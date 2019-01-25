# -*- coding: utf-8 -*-
"""
Created on Sat Jun 30 09:58:01 2018

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

    # run the primary function to update and publish the SDG infomation to a 
    # user content area
    process_sdg_information()
    print(failed_series)
    return

###############################################################################
# ### Collect Series Metadata
# Return all the metadata contained in the seriesMetadata.json file
def get_seriesMetadata():
    try:
        seriesMetadata_json_data = json.load(open(metadata_dir + "/metadata.json"))
        return seriesMetadata_json_data
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None
    
def createGroup(group_info):
    try:
        # Add the Service Definition to the Enterprise site
        item_properties = dict({
            'title': group_info["title"],
            'snippet': group_info["snippet"],
            'description': group_info["description"],
            'tags': ', '.join([group_info["tags"]]),
            'thumbnail': group_info["thumbnail"],
            "isOpenData": True,
            "access": "public",
            "isInvitationOnly": True,
            "protected": True
        })

        # Check if there is a group here
        query_string = "title:'{}' AND owner:{}".format(group_info["title"], online_username)
        search_results = gis_online_connection.groups.search(query_string)
        group = None
        if not search_results:
            return gis_online_connection.groups.create_from_dict(item_properties)
        else:
            group_found = False
            for search_result in search_results:
                if search_result["title"] == group_info["title"]:
                    group_found = True
                    search_result.update(title=group_info["title"], tags=group_info["tags"], description=group_info["description"],
                                         snippet=group_info["snippet"], access="Public", thumbnail=group_info["thumbnail"])
                    return search_result
            # The correct group was not found in the search results add it now
            if not group_found:
                return gis_online_connection.groups.create_from_dict(item_properties)
    except:
        traceback.print_exc()

def process_sdg_information(goal_code=None):
    try:
        series_metadata = get_seriesMetadata()

        create_groups = []
        for series in series_metadata:
            
            ### series = series_metadata[0]
            
            # Determine whether this query only processes a specific goal, target,
            # indicator or series, and if so, whether the current series is *not* 
            # included in the query.
            if goal_code is not None and series["goalCode"] not in goal_code:
                continue

            thumbnail = series["iconUrl"]
            if str(series["goalCode"]) not in create_groups:
                # Create a dictionary containing the annotations for the current item's goal
                goal_properties = dict()
                goal_properties["title"] = "SDG " + str(series["goalCode"])
                goal_properties["snippet"] = series["goalDescription"]
                goal_properties["description"] = series["goalDescription"]
                goal_properties["thumbnail"] = thumbnail
                goal_properties["tags"] = ','.join([goal_properties["title"],'Open Data', 'Hub'])
                createGroup(goal_properties)
                create_groups.append(str(series["goalCode"]))
    except:
        traceback.print_exc()


#set the primary starting point
if __name__ == "__main__":
    main()      

