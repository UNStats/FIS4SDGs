import sys
import json
import pandas as pd
import csv
import numpy as np
#--------------------------------------------
# Set up the global information and variables
#--------------------------------------------

global data_dir                # Directory where csv files are located
global metadata_dir            # Directory where meatadata files are located


#--------------------------------------------
# Set path to data and metadata directories in
# the local branch 
#--------------------------------------------

data_dir = r"../../data/csv/"
metadata_dir = r"../../"
modules_dir = r"../modules/"

#=============================================
# IMPORT MODULES
#=============================================

sys.path.append(modules_dir)
# sys.path

from modules01 import *

#=============================================

#-------------------------------------------------------
# Get the list of all available csv files in long format
#-------------------------------------------------------

long_files = []

listOfFiles = os.listdir(data_dir)  
pattern = "*_long.csv"  
for entry in listOfFiles:  
    if fnmatch.fnmatch(entry, pattern):
        long_files.append(entry)
        
wide_files = []        
for f in long_files:
    wide_files.append(f.replace("long", "wide"))
    

#-----------------------------------------------------------------------------
# List of countreis to be plotted on a map (with XY coordinates)
#------------------------------------------- ----------------------------------

countryListXY = []
with open(metadata_dir+'CountryListXY.txt', newline = '') as countryList:                                                                                          
    countryList = csv.DictReader(countryList, delimiter='\t')
    for row in countryList:
        countryListXY.append(dict(row))
        
country_df = pd.DataFrame.from_records(countryListXY)

country_df.rename(columns={'geoAreaCode': 'GeoArea_Code', 'geoAreaName': 'GeoArea_Desc'}, inplace=True)


#-----------------------------------------------------------------------------
# Analyze long file
#-----------------------------------------------------------------------------


for i in range(len(long_files)):
    
    f = long_files[i]
    #f = '1.1.1-SI_POV_EMP1_long.csv'


    long_data = []
    with open(data_dir+f, newline = '') as dataTable:                                                                                          
        dataTable = csv.DictReader(dataTable, delimiter=',')
        for row in dataTable:
            long_data.append(dict(row))
    
    long_data[0]
    
    long_df = pd.DataFrame.from_records(long_data)
    
    long_df.Year = long_df.Year.astype(float).astype(int)
    
    long_df.columns
    
    long_df[['Year']].drop_duplicates()
    
    #-------------------------------------------------------
    # create vectors identifying Series, Geo, Dimensions, Attributes
    #-------------------------------------------------------
    
    series_cols = ['GoalCode', 'GoalDesc', 
                    'TargetCode', 'TargetDesc', 
                    'IndicatorCode','IndicatorDesc', 'IndicatorTier', 
                    'SeriesCode', 'SeriesDesc','SeriesRelease', 'Units_Code',
                    'Units_Desc']
    
    geo_cols = ['GeoArea_Code', 'GeoArea_Desc', 'ISO3CD', 'X', 'Y']
    
    
    notes_cols = ['Nature_Code','Nature_Desc','Source','Footnotes','TimeDetail']
        
    dimension_columns = list(long_df.columns)
    dimension_columns = [x for x in dimension_columns if x not in series_cols]   
    dimension_columns = [x for x in dimension_columns if x not in geo_cols]   
    dimension_columns = [x for x in dimension_columns if x not in notes_cols] 
    dimension_columns = [x for x in dimension_columns if x not in ('Value', 'ValueType', 'Year')]     
      
    
    key_cols = series_cols + geo_cols + dimension_columns
    
    slice_cols = series_cols + dimension_columns
    
    #-------------------------------------------------------
    # Prepare footnotes for pivoting
    #-------------------------------------------------------
    grouped_by_fn = long_df[key_cols +  ['Year','Footnotes']].groupby(key_cols + ['Footnotes'])
    
    footnotes = []
    for  name, group in grouped_by_fn:
        footnote_str =  list(group['Footnotes'])
        if(len(footnote_str[0])>0):
            fn_key = group[key_cols + ['Footnotes']].drop_duplicates().to_dict('records')
            fn_key[0]['FN_range'] = '[' + year_intervals(list(group['Year'])) + ']'
            footnotes = footnotes + fn_key
    
    footnotes_df = pd.DataFrame(footnotes)
    
    footnotes = []
    grouped_by_fn_2 = footnotes_df.groupby(key_cols)
    for  name, group in grouped_by_fn_2:
        
        fn_key = group[key_cols].drop_duplicates().to_dict('records')
        group_shape = group.shape
        if group_shape[0] == 1 :
            x = group['Footnotes'].values[0]
        else:
            x = group[['FN_range', 'Footnotes']].apply(lambda x: ': '.join(x), axis=1).values
            x = ' // '.join(map(str, x)) 
            
        fn_key[0]['Footnote'] = x
        footnotes = footnotes + fn_key
        
    
    footnotes_df = pd.DataFrame(footnotes)
    #-------------------------------------------------------
    # Prepare sources for pivoting
    #-------------------------------------------------------
    grouped_by_sr = long_df[key_cols +  ['Year','Source']].groupby(key_cols + ['Source'])
    
    sources = []
    for  name, group in grouped_by_sr:
        sources_str =  list(group['Source'])
        if(len(sources_str[0])>0):
            sr_key = group[key_cols + ['Source']].drop_duplicates().to_dict('records')
            sr_key[0]['Source_range'] = '[' + year_intervals(list(group['Year'])) + ']'
            sources = sources + sr_key
    
    sources_df = pd.DataFrame(sources)
    
    sources = []
    grouped_by_sr_2 = sources_df.groupby(key_cols)
    for  name, group in grouped_by_sr_2:
        
        sr_key = group[key_cols].drop_duplicates().to_dict('records')
        group_shape = group.shape
        if group_shape[0] == 1 :
            x = group['Source'].values[0]
        else:
            x = group[['Source_range', 'Source']].apply(lambda x: ': '.join(x), axis=1).values
            x = ' // '.join(map(str, x)) 
            
        sr_key[0]['Source'] = x
        sources = sources + sr_key
        
    sources_df = pd.DataFrame(sources)
    #-------------------------------------------------------
    # Prepare nature for pivoting
    #-------------------------------------------------------
    grouped_by_nt = long_df[key_cols +  ['Year','Nature_Desc']].groupby(key_cols + ['Nature_Desc'])
    
    nature = []
    for  name, group in grouped_by_nt:
        nature_str =  list(group['Nature_Desc'])
        if(len(nature_str[0])>0):
            nt_key = group[key_cols + ['Nature_Desc']].drop_duplicates().to_dict('records')
            nt_key[0]['Nature_range'] = '[' + year_intervals(list(group['Year'])) + ']'
            nature = nature + nt_key
    
    nature_df = pd.DataFrame(nature)
    
    nature = []
    grouped_by_nt_2 = nature_df.groupby(key_cols)
    for  name, group in grouped_by_nt_2:
        
        nt_key = group[key_cols].drop_duplicates().to_dict('records')
        group_shape = group.shape
        if group_shape[0] == 1 :
            x = group['Nature_Desc'].values[0]
        else:
            x = group[['Nature_range', 'Nature_Desc']].apply(lambda x: ': '.join(x), axis=1).values
            x = ' // '.join(map(str, x)) 
            
        nt_key[0]['Nature'] = x
        nature = nature + nt_key
        
        
    nature_df = pd.DataFrame(nature)
    
    
    #-------------------------------------------------------
    # Prepare latest year for pivoting
    #-------------------------------------------------------
    
    idx = long_df.groupby(key_cols)['Year'].transform(max) == long_df['Year']
    
    latest_df = long_df[key_cols + ['Year','Value']][idx]
    
    latest_df.rename(columns={'Year': 'Latest_Year', 'Value': 'Latest_Value'}, inplace=True)
    
    export_csv = latest_df.to_csv ('test_latest.csv', 
                                             index = None, 
                                             header=True,
                                             encoding='utf-8',
                                             quoting=csv.QUOTE_NONNUMERIC)
    
        
    
    #-------------------------------------------------------
    # Create pivot table
    #-------------------------------------------------------
    
    pivot_table = pd.pivot_table(long_df,
                                 index=key_cols,
                                 columns = ['Year'],
                                 values = ['Value'],
                                 aggfunc = lambda x: ''.join(str(v) for v in x))
    
    pivot_table = pivot_table.replace(np.nan, '', regex=True)
    
    
    #------------------------------------------------------
    # Define new column headings (since this is multi-index)
    #------------------------------------------------------
    
    new_header = key_cols[:] 
    
    header_elements = pivot_table.columns
    for c in header_elements:
        new_header.append(c[0]+"_"+ str(c[1]))
    
    
    pivot_table = pivot_table.reset_index()
    
    pivot_table.columns = [''.join(str(col)).strip() for col in pivot_table.columns.values]
    
    pivot_table.columns = new_header
    
    
    #-------------------------------------------------------
    # Add latest year columns to pivot table
    #-------------------------------------------------------
            
    pivot_2 = pd.merge(pivot_table, 
                       latest_df[key_cols +['Latest_Year','Latest_Value']], 
                       how='outer', 
                       on=key_cols)
    
    pivot_3 = pd.merge(pivot_2, 
                       nature_df, 
                       how='outer', 
                       on=key_cols)
    
    
    pivot_4 = pd.merge(pivot_3, 
                       sources_df, 
                       how='outer', 
                       on=key_cols)
         
    
    pivot_5 = pd.merge(pivot_4, 
                       footnotes_df, 
                       how='outer', 
                       on=key_cols)
    
    export_csv = pivot_5.to_csv ('test_pivot.csv', 
                                             index = None, 
                                             header=True,
                                             encoding='utf-8',
                                             quoting=csv.QUOTE_NONNUMERIC)
    
    
    #-------------------------------------------------------
    # Add countries without data (so they can be displayed on a map)
    #-------------------------------------------------------
    
    error_log = []
    
    try:
        
        slice_key = pivot_2[slice_cols].copy()
        slice_key = slice_key.drop_duplicates()
        
        country_key = pivot_2[geo_cols].copy()
        country_key = country_key.drop_duplicates()
        
        # Add 
        
        country_key = country_key.append(country_df[geo_cols]).drop_duplicates()
        #--------------------------------------------------------
            
        def cartesian_product_basic(left, right):
            return (
               left.assign(key=1).merge(right.assign(key=1), on='key').drop('key', 1))
        
        full_key = cartesian_product_basic(country_key,slice_key)
        
        #  export_csv = x.to_csv ('test_cartesian.csv', index = None, header=True) #Don't forget to add '.csv' at the end of the path
       
       
        pivot_6 = pd.merge(full_key, pivot_5, how='left', on=key_cols)
             
       
        #-------------------------------------------------------
        # Export to csv file
        #-------------------------------------------------------
        
        export_csv = pivot_6.to_csv (data_dir + wide_files[i], 
                                     index = None, 
                                     header=True,
                                     encoding='utf-8',
                                     quoting=csv.QUOTE_NONNUMERIC)
        #------------------------------------------------------
        
        
        print("====FINISHED PIVOTING FILE " + f + "(" + str(i) + " of " + str(len(long_files)) + ")")
    
    
    except:
        
        print('===== ' + f + ' COULD NOT BE WRITTEN TO PIVOT FILE=====')
        error_log.append(f)

