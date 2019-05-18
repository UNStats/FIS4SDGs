import sys
import os
import csv
import fnmatch
import getpass
from arcgis.gis import GIS
import json
import pandas as pd
import numpy as np

from modules01 import *


data_dir = r"../../data/csv/"
metadata_dir = r"../../"
modules_dir = r"../modules/"

#---------------------------------------------------------------

def pivot(f,regions_catalog, long_df_regions, geo_cols2,key_cols2,slice_cols, pivot_file_name ):    
  
    
    regions_footnotes_df = collapse_footnotes(long_df_regions, key_cols2,'Footnotes', 'Year')
    regions_sources_df = collapse_footnotes(long_df_regions, key_cols2,'Source', 'Year')
    regions_nature_df = collapse_footnotes(long_df_regions, key_cols2,'Nature_Desc', 'Year')
        
    

    #-------------------------------------------------------
    # Prepare latest year for pivoting
    #-------------------------------------------------------
    
    idx = long_df_regions.groupby(key_cols2)['Year'].transform(max) == long_df_regions['Year']
    
    latest_df = long_df_regions[key_cols2 + ['Year','Value']][idx]
    
    latest_df.rename(columns={'Year': 'Latest_Year', 'Value': 'Latest_Value'}, inplace=True)
   
    
    #-------------------------------------------------------
    # Create pivot table
    #-------------------------------------------------------
    
    pivot_table = pd.pivot_table(long_df_regions,
                                 index=key_cols2,
                                 columns = ['Year'],
                                 values = ['Value'],
                                 aggfunc = lambda x: ''.join(str(v) for v in x))
    
    pivot_table = pivot_table.replace(np.nan, '', regex=True)
    
    
    #------------------------------------------------------
    # Define new column headings (since this is multi-index)
    #------------------------------------------------------
    
    new_header = key_cols2[:] 
    
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
                       latest_df[key_cols2 +['Latest_Year','Latest_Value']], 
                       how='outer', 
                       on=key_cols2)

    #--------------------------------------------------------
    slice_key = pivot_2[slice_cols].copy()
    slice_key = slice_key.drop_duplicates()
    
    country_key = pivot_2[geo_cols2].copy()
    country_key = country_key.drop_duplicates()
    
    # Add 
    
    country_key = country_key.append(regions_catalog[geo_cols2]).drop_duplicates()
    
      
    def cartesian_product_basic(left, right):
        return (
           left.assign(key=1).merge(right.assign(key=1), on='key').drop('key', 1))
    
    full_key = cartesian_product_basic(country_key,slice_key)
    
    #--------------------------------------------------------
    
    if not regions_nature_df.empty:
        pivot_2 = pd.merge(pivot_2, 
                           regions_nature_df, 
                           how='outer', 
                           on=key_cols2)
    
    
    if not regions_sources_df.empty:
        pivot_2 = pd.merge(pivot_2, 
                           regions_sources_df, 
                           how='outer', 
                           on=key_cols2)
         
    if not regions_footnotes_df.empty:
        pivot_2 = pd.merge(pivot_2, 
                           regions_footnotes_df, 
                           how='outer', 
                           on=key_cols2)
    
    
    #-------------------------------------------------------
    # Add countries without data (so they can be displayed on a map)
    #-------------------------------------------------------
    
    error_log = []
    
    try:
        
       
        pivot_2 = pd.merge(full_key, pivot_2, how='left', on=key_cols2)
        
        
        pivot_2['GeoArea_Code'] = pivot_2['GeoArea_Code'].astype('int')
        pivot_2 = pivot_2.sort_values(by=['GeoArea_Code'])
        pivot_2['GeoArea_Code'] = pivot_2['GeoArea_Code'].astype('str')

             
       
        #-------------------------------------------------------
        # Export to csv file
        #-------------------------------------------------------
        
        export_csv = pivot_2.to_csv (data_dir + pivot_file_name, 
                                     index = None, 
                                     header=True,
                                     encoding='utf-8',
                                     quoting=csv.QUOTE_NONNUMERIC)
        #------------------------------------------------------
        
        
        print('finished pivoting series ' + f )
    
    except:
        
        print('===== COULD NOT WRITE TO PIVOT for file ' + f +' =====')
        