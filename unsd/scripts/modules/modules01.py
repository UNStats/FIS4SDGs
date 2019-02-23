import sys
import os
import csv
import fnmatch
import getpass
from arcgis.gis import GIS
import json

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
        
    
def get_file_catalog (dir_path, pattern = '*'):
    
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
        
def get_csv_metadata(file_list, key_list, dir_path = ''):

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
        
def get_sdg_colors(series_metadata):
    """Extract color schemes from current metadata.json file"""
    
    try:
        
        sdg_colors = list()

        for gg in  list(range(17+1)):
            for item in series_metadata:
                if(item['goalCode']==gg):
                    gg_dict = {k: item[k] for k in ('hex','rgb','iconUrl','ColorScheme','ColorSchemeCredits')}
                    gg_dict = {'GoalCode': gg, **gg_dict}
                    sdg_colors.append(gg_dict)
                    break
        
        return sdg_colors
    
    except:
        print("Unexpected error:", sys.exc_info()[0]) 
        return None

#----------------------------------------------------------------
        
def add_tags_to_csv_metadata(csv_metadata, series_metadata):
    """Add tags to csv metadata from current metadata.json file"""
    
    try:
        
        l = list()
        
        for item in csv_metadata:
            for m in series_metadata:
                t = list()
                if(m['seriesCode']==item['SeriesCode']):
                    t = m['TAGS']
                    break
            item_dict = {'Tags': t, **item}
            l.append(item_dict)
        return l
    
    except:
        print("Unexpected error:", sys.exc_info()[0]) 
        return None
    

