import sys
import os
import csv
import fnmatch
import getpass
from arcgis.gis import GIS
import json
import pandas as pd

#---------------------------------------------------------------

def get_series_metadata(file, print_first_element = True):    
    
    """ Get json metadata file """
    
    try:
        series_metadata = json.load(open(file))
        if(print_first_element==True):
            print("\n----This is an example of a series_metadata element----")
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
    

#----------------------------------------------------------------
     
def year_intervals (years_list):
    """ Find the coverage of an ordered list of years"""
    
    #years_list = [1995,1996, 2000,2001,2002,2003,2004]
    
    years_list = list(map(float, years_list))
    
    years_list = list(map(int, years_list))
    
    n = len(years_list)
    
    start_y = list()
    end_y = list()
    
    start_y.append(years_list[0])
    
    if n > 1:
        for i in range(n-1):
            if(years_list[i+1] - years_list[i]>1):
                start_y.append(years_list[i+1])
                end_y.append(years_list[i])
    
    end_y.append(years_list[n-1])
    
    interval_yy = list()
    
    for i in range(len(start_y)):

        if  end_y[i] - start_y[i]> 0 :
            interval_yy.append(str(start_y[i]) + '-' + str(end_y[i]))
        else:
            interval_yy.append(str(start_y[i]))

    
    x = ",".join(interval_yy)
    return(x)

#-------------------------------------------------------------------
  
def collapse_footnotes(df, key_cols, footnote_coln, year_coln):
    """ collapse footnotes for pivoting"""
    grouped_by_fn = df[key_cols +  [year_coln,footnote_coln]].groupby(key_cols + [footnote_coln])
    
    footnotes = []
    for  name, group in grouped_by_fn:
        footnote_str =  list(group[footnote_coln])
        if(len(footnote_str[0])>0):
            fn_key = group[key_cols + [footnote_coln]].drop_duplicates().to_dict('records')
            fn_key[0][footnote_coln + '_range'] = '[' + year_intervals(list(group[year_coln])) + ']'
            footnotes = footnotes + fn_key
    
    footnotes_df = pd.DataFrame(footnotes)
    
    if not footnotes_df.empty:

        footnotes = []
        grouped_by_fn_2 = footnotes_df.groupby(key_cols)
        for  name, group in grouped_by_fn_2:
            
            fn_key = group[key_cols].drop_duplicates().to_dict('records')
            group_shape = group.shape
            if group_shape[0] == 1 :
                x = group[footnote_coln].values[0]
            else:
                x = group[[footnote_coln+'_range', footnote_coln]].apply(lambda x: ': '.join(x), axis=1).values
                x = ' // '.join(map(str, x)) 
                
            fn_key[0][footnote_coln] = x
            footnotes = footnotes + fn_key
            
        
        footnotes_df = pd.DataFrame(footnotes)
    
    return(footnotes_df)