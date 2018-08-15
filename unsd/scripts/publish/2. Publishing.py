# ## Process the SDG Data Items
# The purpose of this notebook is to illustrate how to use the SDG Metadata API in conjunction with local CSV files to
# publish spatial data to ArcGIS Online.  While this example has some elements that are specific to the UNSD workflow it
# is generic enough to show how to loop and use the API for publishing.  You may to need add or update workflows around
# publishing to meet your exact needs and working environments.

# ### Import python libraries
import copy
# used to prompt for user input
# when using this script internally, you may remove this and simply hard code in your username and password
import getpass
import json
import os
import re
import sys
import time
import traceback
import urllib
import urllib.request as request
import urllib.request as urlopen
from datetime import datetime
import requests
# this helps us do some debugging within the Python Notebook
# another optional component
from IPython.display import display
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

# set up the global information and variables
def main():
    # set up the global information and variables
    global open_data_group
    global open_data_group_prod
    global online_username
    global online_username_admin
    global gis_online_connection

    # ### Create a connection to your ArcGIS Online Organization
    # This will rely on using the ArcGIS API for python to connect to your ArcGIS Online Organization to publish and
    # manage data.  For more information about this python library visit the developer
    # resources at [https://developers.arcgis.com/python/](https://developers.arcgis.com/python/]
    online_username = input('Username: ')
    online_password = getpass.getpass('Password: ')

    online_username_admin = "unstats_admin"
    online_connection = "https://www.arcgis.com"
    gis_online_connection = GIS(online_connection, online_username, online_password)

    # metadata_url:  This is the metadata for the API will provide the tags, icons and color information
    # Get information from the local branch
    data_dir = r"FIS4SDGs/csv/"
    metadata_dir = r"FIS4SDGs/json/"

    # open_data_group_id:  Provide the Group ID from ArcGIS Online the Data will be shared with
    #open_data_group_stage_id = '967dbf64d680450eaf424ac4a38799ad' #Travis
    open_data_group_stage_id = 'ad013d2911184063a0f0c97d252daf32'  #Luis
    open_data_group_prod_id = '15c1671f5fbc4a00b1a359d51ea6a546'
    open_data_group = gis_online_connection.groups.get(open_data_group_stage_id)
    open_data_group_prod = gis_online_connection.groups.get(open_data_group_prod_id)

    #run the primary function to update and publish the SDG infomation to a user content area
    promote_sdg()
    return

def promote_sdg(goal_code=None, 
                indicator_code=None, 
                target_code=None, 
                series_code=None,
                property_update_only=False):
    try:
        ## Production Site Changes
        #  Search all the Items in Production Open Data Group
        user = gis_online_connection.users.get(online_username)
        admin_user = gis_online_connection.users.get(online_username_admin)
        if admin_user is None:
            return

        user_items = admin_user.items(folder='Open Data', max_items=800)
        for item in user_items:
            #  Move these items into Archive folder under the Admin User
            print('Moving ' + item.title + ' to archive folder')
            item.move(folder="Historic Data", owner=online_username_admin)

            #  Unshare the Items from Open Data Group (Production)
            display('unsharing item ' + item.title + " from the open data group") 
            item.unshare(open_data_group_prod["id"])

            #  Update Tags (Remove Current add Historic)
            item_properties = {}
            item_properties["tags"] = item.tags
            if 'Current' in item_properties["tags"]:
                item_properties["tags"] = item_properties["tags"].remove('Current');

            item_properties["tags"].append('Historic');
            item.update(item_properties=item_properties)

            # Mark this item as depracated
            set_content_status(update_item=item,authoratative=False)

        ##   Staging Site Changes
        #  Get all the Items in the Open Data Folder
        user_items = user.items(folder='Open Data', max_items=800)
        for item in user_items:
            #Move all the CSV Files to the Open Data Folder of the Admin User
            # This will also move the Feature Service Layer
            if item.type == 'CSV':
                # Assign Item to the Admin User
                display('reassigning item ' + item.title + ' from ' + online_username + ' to ' + online_username_admin)
                item.reassign_to(online_username_admin, 'Open Data')

        # Update the Items in the Open Data Folder of the Admin User
        user_items = admin_user.items(folder='Open Data', max_items=800)
        for item in user_items:
            # Update Sharing to Public, Share with Open Data Group     
            if item.type != 'CSV':
                display('updating sharing for item ' + item.title) 
                item.share(everyone=True, org=True, groups=open_data_group_prod["id"],
                            allow_members_to_edit=False)
                
                # Disable Editing on the Feature Service
                display('disable editing for ' + item.title)
                item_flc = FeatureLayerCollection.fromitem(item)
                update_dict2 = {"capabilities": "Query, Extract"}
                item_flc.manager.update_definition(update_dict2)

            #  Unshare from Staging Group
            display('unsharing item ' + item.title + " from the staging group") 
            item.unshare(open_data_group["id"])

            display('enabling delete protection for: ' + item.title)
            item.protect(enable=True)

            # Tag as Current
            display('updating item properties for ' + item.title)
            item_properties = dict()
            item_properties["tags"] = item.tags.append('Current')
            item.update(item_properties=item_properties)

            # Mark this item as authoratative
            display('marking item ' + item.title + " as authortative")
            set_content_status(update_item=item,authoratative=True)

    except:
        traceback.print_exc()
    return

def set_content_status(update_item, authoratative=True):
    sharing_url = gis_online_connection._url + "/sharing/rest/content/items/" + update_item.id + "/setContentStatus"
    sharing_params = {'f': 'json', 'token': gis_online_connection._con.token,
                        'status': 'org_authoritative' if authoratative else 'deprecated',
                        'clearEmptyFields': 'false'}
    r = requests.post(sharing_url, data=sharing_params)
    sharing_json_data = json.loads(r.content.decode("UTF-8"))

#set the primary starting point
if __name__ == "__main__":
    main()      
