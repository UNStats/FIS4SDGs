import sys
import getpass
from arcgis.gis import GIS
import json

#----------------------------------------------------------------

def connect_to_arcGIS():

    """Open connection to ArcGIS Online Organization"""
        
    online_username = input('Username: ')
    online_password = getpass.getpass('Password: ')
    online_connection = "https://www.arcgis.com"
    gis_online_connection = GIS(online_connection, 
                                online_username, 
                                online_password)
    
    return online_username, gis_online_connection
    
#----------------------------------------------------------------
    
def open_data_group(gis_online_connection,id):
    
    open_data_group = gis_online_connection.groups.get(id)
    return (open_data_group)
   
    
#----------------------------------------------------------------
    
def cleanup_staging_folder(user_items):

    """ Cleanup staging folder for Open Data (delete everything in the staging folder for Open Data)"""
    
    if input("Do you want to cleanup your staging folder for Open Data? (y/n)") == "y":
        if input("Are you sure? (y/n)") == "y":
            for item in user_items:
                print('deleting item ' + item.title)
                item.delete()
        else: print('Cleanup of staging forlder for Open Data was canceled') 
    else:
        print('Cleanup of staging forlder for Open Data was canceled')      
        
        
#----------------------------------------------------------------

def get_layer_info_template(file, print_first_element = True):  
    
    """ Get layer info template """
    
    try:
        layer_info_template = json.load(open(file))
        if(print_first_element==True):
            print("/n----This is the layer info template ----")
            print(layer_info_template)
        return layer_info_template
    except:
        print("Unexpected error:", sys.exc_info()[0]) 
        return None
        
