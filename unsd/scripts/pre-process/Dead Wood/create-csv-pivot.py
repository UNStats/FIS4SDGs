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

#=============================================
# INPUT USER PARAMETERS
#=============================================
property_update_only = False
update_symbology = True

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

from modules03 import *

#=============================================
# GET METADATA
#=============================================

long_files = get_file_catalog(data_dir, pattern = '*_long.csv')

       
wide_files = []        
for f in long_files:
    wide_files.append(f.replace("long", "wide"))


regions_catalog = []
cities_catalog=[]

#-----------------------------------------------------------------------------
# Analyze long file to get regions and cities catalogs
#-----------------------------------------------------------------------------

for i in range(len(long_files)):

    f = long_files[i]
    #f = '10.a.1-TM_TRF_ZERO_long.csv'
    
    
    long_data = []
    with open(data_dir+f, newline = '') as dataTable:                                                                                          
        dataTable = csv.DictReader(dataTable, delimiter=',')
        for row in dataTable:
            long_data.append(dict(row))
            
    if not long_data:
        print(f + ' contains no data')
        continue
    
    
    long_df = pd.DataFrame.from_records(long_data)
    
    long_df.Year = long_df.Year.astype(float).astype(int)
    
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
    
    #drop ISO3D, X, and Y if not present:
    geo_cols = [x for x in geo_cols if x in list(long_df.columns)] 
    
    
    notes_cols = ['Nature_Code','Nature_Desc','Source','Footnotes','TimeDetail']
        
    dimension_columns = list(long_df.columns)
    dimension_columns = [x for x in dimension_columns if x not in series_cols]   
    dimension_columns = [x for x in dimension_columns if x not in geo_cols]   
    dimension_columns = [x for x in dimension_columns if x not in notes_cols] 
    dimension_columns = [x for x in dimension_columns if x not in ('Value', 'ValueType', 'Year')]     
      
    
    key_cols = series_cols + geo_cols + dimension_columns
    
    slice_cols = series_cols + dimension_columns
    
    #------------------------------------------------------
    # Build list of regions contained in the current csv
    #------------------------------------------------------
    
    x = long_df[geo_cols].drop_duplicates().copy()
    if {'X'}.issubset(list(x.columns)):
        x = x.loc[(x['X'] == "") & (~x['GeoArea_Code'].isin(['412','729']))]
    regions_catalog.append(x[['GeoArea_Code','GeoArea_Desc']])
    
    
    #------------------------------------------------------
    # Build list of cities contained in the current csv
    #------------------------------------------------------
    if {'Cities_Code','Cities_Desc'}.issubset(list(long_df.columns)):
        x = long_df[geo_cols+['Cities_Code','Cities_Desc']].drop_duplicates().copy()
        x = x.loc[(x['Cities_Code'] != "NOCITI")]
        cities_catalog.append(x[['GeoArea_Code','GeoArea_Desc','ISO3CD','Cities_Code','Cities_Desc']])
        
    print('finished analyzing series ' + f + ' to create regions catalog')
    


# see pd.concat documentation for more info
if cities_catalog:
    cities_catalog = pd.concat(cities_catalog).drop_duplicates()
    cities_catalog['GeoArea_Code'] = cities_catalog['GeoArea_Code'].astype('int')
    cities_catalog = cities_catalog.sort_values(by=['GeoArea_Code'])
    cities_catalog['GeoArea_Code'] = cities_catalog['GeoArea_Code'].astype('str')

regions_catalog = pd.concat(regions_catalog).drop_duplicates()
regions_catalog['GeoArea_Code'] = regions_catalog['GeoArea_Code'].astype('int')
regions_catalog = regions_catalog.sort_values(by=['GeoArea_Code'])
regions_catalog['GeoArea_Code'] = regions_catalog['GeoArea_Code'].astype('str')


#====================================================================================
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


for i in range(119,len(long_files)):
    
    print('\nProcessing ' + str(i) + ' of ' + str(len(long_files)))
    
    f = long_files[i]
    #f = '10.a.1-TM_TRF_ZERO_long.csv'
    
    pivot_file_name = 'region_' + wide_files[i]


    long_data = []
    with open(data_dir+f, newline = '') as dataTable:                                                                                          
        dataTable = csv.DictReader(dataTable, delimiter=',')
        for row in dataTable:
            long_data.append(dict(row))
            
    if not long_data:
        print(f + ' contains no data')
        continue
    
    long_data[0]
    
    long_df = pd.DataFrame.from_records(long_data)
    
    long_df.Year = long_df.Year.astype(float).astype(int)
    
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
    geo_cols2 = ['GeoArea_Code', 'GeoArea_Desc']
    
    #drop ISO3D, X, and Y if not present:
    geo_cols = [x for x in geo_cols if x in list(long_df.columns)] 
    
    
    notes_cols = ['Nature_Code','Nature_Desc','Source','Footnotes','TimeDetail']
        
    dimension_columns = list(long_df.columns)
    dimension_columns = [x for x in dimension_columns if x not in series_cols]   
    dimension_columns = [x for x in dimension_columns if x not in geo_cols]   
    dimension_columns = [x for x in dimension_columns if x not in notes_cols] 
    dimension_columns = [x for x in dimension_columns if x not in ('Value', 'ValueType', 'Year')]     
      
    
    key_cols = series_cols + geo_cols + dimension_columns
    key_cols2 = series_cols + geo_cols2 + dimension_columns
    
    slice_cols = series_cols + dimension_columns
    
    has_cities = {'Cities_Code','Cities_Desc'}.issubset(dimension_columns)
    
    long_df_regions = pd.merge(regions_catalog, 
                           long_df,
                           how='left', 
                           on=geo_cols2)
    

    has_regions = pd.merge(regions_catalog[['GeoArea_Code']], 
                           long_df[['GeoArea_Code']],
                           how='inner', 
                           on='GeoArea_Code')
    
       
    if not has_regions.empty:
        pivot(f, regions_catalog, long_df_regions, geo_cols2,key_cols2,slice_cols, 'reg_'+wide_files[i] ) 
    
    if has_cities:
        pivot(f, country_df.loc[country_df['X'] !=''], 
              long_df.loc[ (long_df['Cities_Code'] == "NOCITI") & (long_df['X'] !='')], geo_cols,key_cols,slice_cols, 'country_'+wide_files[i] ) 
    else:
        if {'X'}.issubset(list(long_df.columns)):
            pivot(f, country_df,  long_df.loc[ (long_df['X'] !='')], geo_cols,key_cols,slice_cols, 'country_'+wide_files[i] ) 

    
    
   