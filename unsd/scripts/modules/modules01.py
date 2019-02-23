import sys
import os
import csv
import fnmatch
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
        
#---------------------------------------------------------------

def get_series_metadata(file, print_first_element = True):    
    
    """ Get json metadata file """
    
    try:
        series_metadata = json.load(open(file))
        if(print_first_element==True):
            print("/n----This is an example of a series_metadata element----")
            print(series_metadata[0])
        return series_metadata
    
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None
    
        
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
        
#----------------------------------------------------------------
        
    
def file_catalog (dir_path, pattern = '*'):
    
    """ Create a list of files in a folder """

    try:
        files = list()

        listOfFiles = os.listdir(dir_path)  
        for entry in listOfFiles:  
            if fnmatch.fnmatch(entry, pattern):
                files.append(entry)
        return files
            
    except:
        print("Unexpected error:", sys.exc_info()[0]) 
        return None
        
#----------------------------------------------------------------
        
    
def read_csv_to_list (file, encoding="utf8"):
    
    """ Read a csv file into a list """

    try:
        
        with open(file, encoding=encoding) as f:
            reader = csv.reader(f)
            data = list(reader)
        return data
            
    except:
        print("Unexpected error:", sys.exc_info()[0]) 
        return None
    

#----------------------------------------------------------------
        
    
def read_csv_to_dict (file, encoding="utf8"):
    
    """ Read a csv file into a dict """

    try:
   
        with open(file,  encoding="utf8") as f:
            reader = csv.DictReader(f)
            dict_list = list()
            for line in reader:
                dict_list.append(dict(line))
            return dict_list
    
    except:
        print("Unexpected error:", sys.exc_info()[0]) 
        return None
    

#----------------------------------------------------------------
        
def csv_metadata(file_list, key_list, dir_path = ''):

    "Extract metadata key-value pairs from a list of csv files"

    try:

        metadata_list = list()
    
        for f in file_list:
            temp_dict = read_csv_to_dict(dir_path+f)
            n_rows = len(temp_dict)
            temp_dict = temp_dict[0]
            mini_dict = {k: temp_dict[k] for k in (key_list)}
            mini_dict = {**mini_dict, 'csv_file': f, 'n_rows': n_rows }
            metadata_list.append(mini_dict)
            print("extracting metadata for file " + f)
        
        return metadata_list
    
    except:
        print("Unexpected error:", sys.exc_info()[0]) 
        return None
        


#----------------------------------------------------------------

       
