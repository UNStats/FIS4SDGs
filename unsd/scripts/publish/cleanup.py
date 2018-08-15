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

# ### Create a connection to your ArcGIS Online Organization
# This will rely on using the ArcGIS API for python to connect to your ArcGIS Online Organization to publish and
# manage data.  For more information about this python library visit the developer
# resources at [https://developers.arcgis.com/python/](https://developers.arcgis.com/python/]
online_username = input('Username: ')
online_password = getpass.getpass('Password: ')
online_connection = "https://www.arcgis.com"
gis_online_connection = GIS(online_connection, online_username, online_password)

user = gis_online_connection.users.get(online_username)
admin_user = gis_online_connection.users.get('unstats_admin')
user_items = user.items(folder='Open Data', max_items=800)
for item in user_items:
    display('deleting item: ' + item.title)
    item.protect(enable=False)
    item.delete()

user_items = admin_user.items(folder='Open Data', max_items=800)
for item in user_items:
    display('deleting item: ' + item.title)
    item.protect(enable=False)
    item.delete()

user_items = admin_user.items(folder='Historic Data', max_items=800)
for item in user_items:
    display('deleting item: ' + item.title)
    item.protect(enable=False)
    item.delete()


display('all done')