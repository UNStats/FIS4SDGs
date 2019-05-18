import sys
import os
import getpass
from arcgis.gis import GIS
import json
import copy
import requests


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
    
    if input('Do you want to cleanup your staging folder for Open Data? (y/n)') == 'y':
        if input('Are you sure? (y/n)') == 'y':
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
        
#----------------------------------------------------------------
        
def build_series_card(series_metadata_item):
    """ Build series metadata card """
    
    try:
        s_card = dict()
        s_card['title'] = 'Indicator ' + series_metadata_item['IndicatorCode'] + ': ' + series_metadata_item['SeriesDesc'].replace('%','percent')
        s_card['layer_title'] = series_metadata_item['SeriesDesc'].replace('%','percent').replace(',',' ').replace('/',' ')
        
        snippet = s_card['title']
        
        s_card['snippet'] = (snippet[:250] + '..') if len(snippet) > 250 else snippet
        s_card['description'] =  \
                    '<p><strong>Series ' + series_metadata_item['SeriesCode'] + ': </strong>' + series_metadata_item['SeriesDesc'] + \
                    '/p>' + \
                    '<p><strong>Indicator ' + series_metadata_item['IndicatorCode'] + ': </strong>' + \
                    series_metadata_item['IndicatorDesc'] + \
                    '</p>' + \
                    '<p><strong>Target ' + series_metadata_item['TargetCode'] + ': </strong>' + \
                    series_metadata_item['TargetDesc'] + \
                    '</p>' + \
                    '<p><strong>Goal ' + series_metadata_item['GoalCode'] + ': </strong>' +  \
                    series_metadata_item['GoalDesc'] + \
                    '</p>' +  \
                    '<p><em>Release Version: ' + series_metadata_item['SeriesRelease'] + ' </em>'+ \
                    '</p>' 
        
        series_tags = series_metadata_item['Tags'][:]
        series_tags.append(series_metadata_item['SeriesRelease'])
                
        s_card['tags'] = series_tags
        
        return s_card
    except:
        print('Unexpected error:', sys.exc_info()[0]) 
        return None
        
#----------------------------------------------------------------
        
def find_online_item(title, owner, gis_online_connection, force_find=True):
        
    try:

        # Search for this ArcGIS Online Item
        query_string = "title:'{}' AND owner:{}".format(title, owner)
        print('Searching for ' + title)
        # The search() method returns a list of Item objects that match the 
        # search criteria
        search_results = gis_online_connection.content.search(query_string)
        
        if search_results:
            for item in search_results:
                if item['title'] == title:
                    print(' -- Item ' + title + ' found (simple find)')
                    return item
        
        if force_find:
            user = gis_online_connection.users.get(owner)
            user_items = user.items(folder='Open Data', max_items=800)
            for item in user_items:
                if item['title'] == title:
                    print(' -- Item ' + title + ' found (force find)')
                    return item
            print(' -- Item ' + title + ' not found (force find)')
            return None
        
        print(' -- Item ' + title + ' not found (simple find)')
        return None
    
    except:
        print('Unexpected error:', sys.exc_info()[0])
        return None
        
        
#----------------------------------------------------------------
        
def generate_renderer_infomation(feature_item, 
                                 statistic_field,
                                 layer_info,
                                 color=None):
    try:
        if len(color) == 3:
            color.append(130)  ###---specifies the alpha channel of the color
        
        visual_params = layer_info['layerInfo']
        definition_item = feature_item.layers[0]

        #get the min/max values
        out_statistics= [{'statisticType': 'max',
                          'onStatisticField': statistic_field, 
                          'outStatisticFieldName': statistic_field + '_max'},
                        {'statisticType': 'min',
                         'onStatisticField': statistic_field, 
                         'outStatisticFieldName': statistic_field + '_min'}]
        
        feature_set = definition_item.query(where='1=1',out_statistics=out_statistics)

        max_value = feature_set.features[0].attributes[statistic_field + '_max']
        min_value = feature_set.features[0].attributes[statistic_field + '_min']
        
        visual_params['drawingInfo']['renderer']['visualVariables'][0]['minDataValue'] = min_value
        visual_params['drawingInfo']['renderer']['visualVariables'][0]['maxDataValue'] = max_value

        visual_params['drawingInfo']['renderer']['authoringInfo']['visualVariables'][0]['minSliderValue'] = min_value
        visual_params['drawingInfo']['renderer']['authoringInfo']['visualVariables'][0]['maxSliderValue'] = max_value
        
        visual_params['drawingInfo']['renderer']['classBreakInfos'][0]['symbol']['color'] = color
        visual_params['drawingInfo']['renderer']['transparency'] = 25

        definition_update_params = definition_item.properties
        definition_update_params['drawingInfo']['renderer'] = visual_params['drawingInfo']['renderer']
        if 'editingInfo' in definition_update_params:
            del definition_update_params['editingInfo']
        definition_update_params['capabilities'] = 'Query, Extract, Sync'
        print('Update Feature Service Symbology')
        definition_item.manager.update_definition(definition_update_params)

        return
    except:
        print('Unexpected error in generate_renderer_infomation:', sys.exc_info()[0])
        return None

        
#----------------------------------------------------------------

def publish_csv(series_metadata_item, 
                item_properties, 
                thumbnail,
                layer_info,
                gis_online_connection, 
                data_dir,
                online_username,
                statistic_field = 'Latest_Value',
                property_update_only=False, 
                color=[169,169,169]):
    
    
        # Check if service name is available; if not, update the link
        service_title = series_metadata_item['SeriesCode'] + '_' + series_metadata_item['IndicatorCode'].replace('.','_') + '_' + series_metadata_item['SeriesRelease'].replace('.', '')
        
        service_title_num = 1
        
        while not gis_online_connection.content.is_service_name_available(service_name= service_title, service_type = 'featureService'):
            service_title = series_metadata_item['SeriesCode'] + '_' + series_metadata_item['IndicatorCode'].replace('.','_') + '_' + series_metadata_item['SeriesRelease'].replace('.', '') + \
              '_' + str(service_title_num)
            service_title_num += 1

        file = os.path.join(data_dir, series_metadata_item['csv_file'] )
        
        if os.path.isfile(file):
            csv_item_properties = copy.deepcopy(item_properties)
            csv_item_properties['name'] = service_title
            csv_item_properties['title'] = service_title
            csv_item_properties['type'] = 'CSV'
            csv_item_properties['url'] = ''

            # Does this CSV already exist
            csv_item = find_online_item(csv_item_properties['title'],online_username,gis_online_connection)
            
            if csv_item is None:
                print('Adding CSV File to ArcGIS Online....')
                csv_item = gis_online_connection.content.add(item_properties=csv_item_properties, 
                                                             thumbnail=thumbnail,
                                                             data=file)
                if csv_item is None:
                    return None

                print('Analyze Feature Service....')
                publish_parameters = analyze_csv(csv_item['id'],gis_online_connection)
                if publish_parameters is None:
                    return None
                else:
                    publish_parameters['name'] = csv_item_properties['title']
                    publish_parameters['layerInfo']['name'] = csv_item_properties['layer_title']
                    print('Publishing Feature Service....')
                    csv_lyr = csv_item.publish(publish_parameters=publish_parameters, overwrite=True)

                    # Update the layer infomation with a basic rendering based on the Latest Value
                    # use the hex color from the SDG Metadata for the symbol color
                    
                    generate_renderer_infomation(feature_item=csv_lyr,
                                                 statistic_field = statistic_field,
                                                 layer_info = layer_info,
                                                 color=color) 
            else:
                # Update the Data file for the CSV File
                csv_item.update(item_properties=csv_item_properties, thumbnail=thumbnail, data=file)
                # Find the Feature Service and update the properties
                csv_lyr = find_online_item(csv_item_properties['title'],online_username,gis_online_connection)

            # Move to the Open Data Folder
            if csv_item['ownerFolder'] is None:
                print('Moving CSV to Open Data Folder')
                csv_item.move('Open Data')

            if csv_lyr is not None:
                print('Updating Feature Service metadata....')
                csv_lyr.update(item_properties=item_properties, thumbnail=thumbnail)

                if csv_lyr['ownerFolder'] is None:
                    print('Moving Feature Service to Open Data Folder')
                    csv_lyr.move('Open Data')

                return csv_lyr
            else:
                return None
        else:
            return None
     
#------------------------------------------------------------------------------


def analyze_csv(item_id, gis_online_connection):
    try:
        sharing_url = gis_online_connection._url + '/sharing/rest/content/features/analyze'
        analyze_params = {'f': 'json', 
                          'token': gis_online_connection._con.token,
                          'sourceLocale': 'en-us',
                          'filetype': 'csv', 
                          'itemid': item_id}
        r = requests.post(sharing_url, data=analyze_params)
        analyze_json_data = json.loads(r.content.decode('UTF-8'))
        for field in analyze_json_data['publishParameters']['layerInfo']['fields']:
            field['alias'] = set_field_alias(field['name'])

            # IndicatorCode is coming in as a date Field make the correct
            if field['name'] == 'IndicatorCode':
                field['type'] = 'esriFieldTypeString'
                field['sqlType'] = 'sqlTypeNVarchar'

        # set up some of the layer information for display
        analyze_json_data['publishParameters']['layerInfo']['displayField'] = 'GeoArea_Desc'
        return analyze_json_data['publishParameters']
    except:
        print('Unexpected error:', sys.exc_info()[0])
        return None
    
#------------------------------------------------------------------------------
        
def set_field_alias(field_name):
    if field_name == 'SeriesRelease':
        return 'Series Release'
    if field_name == 'SeriesCode':
        return 'Series Code'
    if field_name == 'SeriesDesc':
        return 'Series Description'
    if field_name == 'GeoArea_Code':
        return 'Geographic Area Code'
    if field_name == 'GeoArea_Desc':
        return 'Geographic Area Name'
    if field_name == 'Latest_Year':
        return 'Latest Year'
    if field_name == 'Latest_Value':
        return 'Latest Value'
    if field_name == 'last_5_years_mean':
        return 'Mean of the Last 5 Years'
    if field_name == 'ISO3CD':
        return 'ISO3 Code'
    if field_name == 'GoalCode':
        return 'Goal Code'
    if field_name == 'GoalDesc':
        return 'Goal Description'
    if field_name == 'TargetCode':
        return 'Target Code'
    if field_name == 'TargetDesc':
        return 'Target Description'
    if field_name == 'IndicatorCode':
        return 'Indicator Code'
    if field_name == 'IndicatorDesc':
        return 'Indicator Description'
    if field_name == 'IndicatorTier':
        return 'Indicator Tier'
    else:
        return field_name.capitalize().replace('_', ' ')
    

#------------------------------------------------------------------------------
    
def update_item_categories(item, goal, target,gis_online_connection):
    update_url = gis_online_connection._url + "/sharing/rest/content/updateItems"
    items = [{item["id"]:{"categories":["/Categories/Goal " + str(goal) + "/Target " + str(target)]}}]
    update_params = {'f': 'json', 
                         'token': gis_online_connection._con.token, 
                         'items': json.dumps(items)}
    r = requests.post(update_url, data=update_params)
    update_json_data = json.loads(r.content.decode("UTF-8"))
    print(update_json_data)