import csv
import json
import urllib3  # allows to access a URL with python
import math
import os
import collections

os.chdir('C:\\Users\\L.GonzalezMorales\\Documents\\GitHub\\FIS4SDGs\\unsd\\') 

release = '2019.Q1.G.01' # Make sure to have the correct release here

error_log = []
     
#-----------------------------------------------------------------------------
# List of countreis to be plotted on a map (with XY coordinates)
#------------------------------------------- ----------------------------------

countryListXY = []
with open('CountryListXY.txt', newline = '') as countryList:                                                                                          
    countryList = csv.DictReader(countryList, delimiter='\t')
    for row in countryList:
        countryListXY.append(dict(row))
        
#print(countryListXY[1])
#for c in countryListXY:

#-------------------------------------------------------
# GET THE LIST OF GOALS, TARGETS, INDICATORS and SERIES
#------------------------------------------------------

# Start by creating a PoolManager() object using urllib3. 
        
http = urllib3.PoolManager()

response = http.request('GET', "https://unstats.un.org/SDGAPI/v1/sdg/Goal/List?includechildren=true")
responseData = json.loads(response.data.decode('UTF-8'))

series_list = []

keys = ["goalCode", 
        "goalDesc",
        "targetCode",
        "targetDesc",
        "indicatorCode",
        "indicatorDesc",
        "indicatorTier",
        "seriesCode",
        "seriesDesc",
        "seriesRelease"
       ]

for g in responseData:
    for t in g['targets']:
        for i in t['indicators']:
            for s in i['series']:
                if s['release'] == release:
                    values = [g['code'], g['title'],
                              t['code'], t['description'], 
                              i['code'], i['description'], i['tier'], 
                              s['code'], s['description'], s['release']]
                    
                    keys_and_values = zip(keys, values)
                    serie_dic = {}
                    for key, value in keys_and_values:
                        serie_dic[key] = value
                    series_list.append(serie_dic)
                        
# Example:  series_list = 
# [{'goalCode': '1',
# 'goalDesc': 'End poverty in all its forms everywhere',
# 'targetCode': '1.1',
# 'targetDesc': 'By 2030, eradicate extreme poverty for all people everywhere, currently measured as people living on less than $1.25 a day',
# 'indicatorCode': '1.1.1',
# 'indicatorDesc': 'Proportion of population below the international poverty line, by sex, age, employment status and geographical location (urban/rural)',
# 'indicatorTier': '1',
# 'seriesCode': 'SI_POV_DAY1',
# 'seriesDesc': 'Proportion of population below international poverty line (%)',
# 'seriesRelease': '2019.Q1.G.01'}, ...]

#------------------------------------------------------
# GET THE DATA FOR EACH SERIES
#------------------------------------------------------

for s in series_list:    
    
# Use this for testing character encoding problem:
# x = [d for d in series_list if d['seriesCode'] == 'SH_STA_BRTC']                    
# for s in x:

    seriesRequest = 'https://unstats.un.org/SDGAPI/v1/sdg/Series/Data?seriesCode=' + s['seriesCode'] + "&pageSize=2"
    
    response = http.request('GET', seriesRequest)
    responseData = json.loads(response.data.decode('UTF-8'))
    
    pageSize = 500
    nPages = math.floor(responseData['totalElements'] / pageSize) + 1
    
    print("series = " + s['seriesCode'] + "; totalElements = ", str(responseData['totalElements'] )+ "; pageSize = " + str(pageSize) + "  Pages = " +  str(nPages))
    
    
    #------------------------------------------------------    
    series_data = []
    
    if responseData['totalElements']>0:
        
        series_attributes = responseData['attributes']
        series_dimensions = responseData['dimensions']
        
        
        for p in range(nPages):
            
            
        
            print("---PROCESSING PAGE " + str(p+1) + " of " + str(nPages))
        
            queryString =  "https://unstats.un.org/SDGAPI/v1/sdg/Series/Data?seriesCode=" + s['seriesCode'] + "&page=" + str(p+1) + "&pageSize=" + str(pageSize)
            
            response = http.request('GET', queryString)
            responseData =  json.loads(response.data.decode('UTF-8'))
            
            if len(responseData['data'])>0:
                series_data = series_data + responseData['data']
                
    #------------------------------------------------------ 
    
    series_dataset = []
        
    for k in [d for d in series_data if d['indicator'][0] == s['indicatorCode']]:  # this is to avoid duplicates in multipurpose indicators
                
        record = collections.OrderedDict()
        
        for ss in s.keys():
            key_name = "%s%s" % (ss[0].upper(), ss[1:])
   
            record[key_name] = s[ss]
            
        value_dimensions = k['dimensions']
        
        for d in value_dimensions.keys():
             dimension_name = d
             dimension_code = value_dimensions[d]
             
             for dd in series_dimensions:
                 if dd['id'] == dimension_name:
                     for cc in dd['codes']:
                         if cc['code'] == dimension_code:
                             dimension_desc = cc['description']
                             continue
                         
             dimension_name = ''.join(x for x in dimension_name.title() if not x.isspace())
             
             record[dimension_name + "_Code"] = dimension_code 
             record[dimension_name + "_Desc"] = dimension_desc
        
        
        value_attributes = k['attributes']
        
        for a in value_attributes.keys():
             attribute_name = a
             attribute_code = value_attributes[a]
             
             for aa in series_attributes:
                 if aa['id'] == attribute_name:
                     for cc in aa['codes']:
                         if cc['code'] == attribute_code:
                             attribute_desc = cc['description']
                             continue
                         
             attribute_name = ''.join(x for x in attribute_name.title() if not x.isspace())
             
             record[attribute_name + "_Code"] = attribute_code 
             record[attribute_name + "_Desc"] = attribute_desc
        
        
                 
        data_items = [ 'geoAreaCode', 'geoAreaName','timePeriodStart', 'time_detail','value', 'valueType', 'source',  'footnotes']
        
        for i in data_items:
            key_name = ''.join(x for x in i.title())
            
            if i == 'geoAreaCode': 
                key_name = 'GeoArea_Code'
            if i == 'geoAreaName': 
                key_name = 'GeoArea_Desc'
            if i == 'source': 
                key_name = 'Source'
            if i == 'timePeriodStart': 
                key_name = 'Year'
            if i == 'time_detail':
                key_name = 'TimeDetail'
            if i == 'footnotes' : 
                key_name = 'Footnotes'
                k[i] =  "; ".join(k[i])
            if i == 'value' : 
                key_name = 'Value'
            if i == 'valueType': 
                key_name = 'ValueType'
                
            record[key_name] = k[i]  
        
        for xy in countryListXY:
            if xy['geoAreaCode'] == record['GeoArea_Code']:
                record['ISO3CD'] = xy['ISO3CD']
                record['X'] = xy['X']
                record['Y'] = xy['Y']
            continue
        
        series_dataset.append(record)
     
    try:
        with open('data\\csv\\'+ record['IndicatorCode'] + "-" + s['seriesCode']+'_long.csv', 'w', newline='') as outfile:
            fp = csv.DictWriter(outfile, series_dataset[0].keys(), quoting=csv.QUOTE_NONNUMERIC)
            fp.writeheader()
            fp.writerows(series_dataset)
            
            print('=====FINISHED WRITING SERIES ' + record['SeriesCode'] + ' TO FILE=====')
            
              
          
    
    except:
        
        error_log.append(record['SeriesCode'])
        
        print('=====SERIES ' + record['SeriesCode'] + ' COULD NOT BE WRITTEN TO FILE=====')
        

#    with open('data\\csv\\'+ record['IndicatorCode'] + "-" + s['seriesCode']+'_long.csv', 'w', newline='') as outfile:
#        fp = csv.DictWriter(outfile, series_dataset[0].keys())
#        fp.writeheader()
#        fp.writerows(series_dataset)
#        
#        print('=====FINISHED WRITING SERIES ' + record['SeriesCode'] + ' TO FILE=====')

        

      