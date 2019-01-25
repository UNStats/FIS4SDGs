import csv
import json
import urllib3  # allows to access a URL with python
import urllib
import re
import statistics
import math
#--------------------------------------------------------------------        

release = '2018.Q4.G.02' # Make sure to have the correct release here

#-----------------------------------------
# Functions
#-----------------------------------------

# Commercial rounding
def round_KFM(x, n):
    posneg = math.copysign(1, x)
    z = abs(x)*10**n
    z = z + 0.5
    z = math.trunc(z)
    z = z/10**n
    result = z * posneg
    return result
    
#print(round_KFM(3.5023,2))

#-----------------------------------------

# The parseTree function iterates through the tree and creates a flat array of countries

def parseTree(obj):
    if (obj['type'] == 'Country'):
        #print(obj['geoAreaName'], '(C)')
        countryArray.append(obj)
    else:
        #print(obj['geoAreaName'], '(R)')
        if (obj['children'] is not None):
            for child in obj['children']:
                parseTree(child)


#-----------------------------------------
# READ FACT BUILDER CONDITIONS
#-----------------------------------------

fact_builder = []
with open('CountryProfileBuilder.txt', newline = '') as countryProfileBuilder:                                                                                          
    country_profile_builder = csv.DictReader(countryProfileBuilder, delimiter='\t')
    for row in country_profile_builder:
        fact_builder.append(dict(row))
        
print(fact_builder[1])

#-----------------------------------------
# CREATE LIST OF COUNTRIES
#-----------------------------------------
#Start by creating a PoolManager() object using urllib3. It's that object that you can use to make requests to a website.
http = urllib3.PoolManager()

#Make a GET request using the http object that you just created to the DoTA API.
geoAreas = http.request('GET', 'https://unstats.un.org/SDGAPI/v1/sdg/GeoArea/Tree')
geoAreas_tree = json.loads(geoAreas.data.decode('UTF-8'))


world_tree = geoAreas_tree[0]

#print(world_tree['geoAreaName'])

#for x in world_tree['children']:
#    print("-"*10)
#    print(x)

# The parseTree function iterates through the tree and creates a flat array of countries

global countryArray
countryArray = []

for area in world_tree['children']:
    parseTree(area)

#print(countryArray)
#for country in countryArray:
#    print(country['geoAreaCode'], " - ", country['geoAreaName'])

    
print("total number or countries: ", len(countryArray))

#-----------------------------------------------
# GET THE LIST OF GOALS, TARGETS AND INDICATORS
#-----------------------------------------------

response = http.request('GET', "https://unstats.un.org/SDGAPI/v1/sdg/Goal/List?includechildren=true")
indicator_framework = json.loads(response.data.decode('UTF-8'))

#print(indicator_framework[0])

series_list = []

keys = ["goalCode", 
        "goalDesc",
        "targetCode",
        "targetDesc",
        "indicatorCode",
        "indicatorDesc",
        "indicatorTier",
        "seriesCode",
        "seriesDesc"
       ]

for g in indicator_framework:
    for t in g['targets']:
        for i in t['indicators']:
            for s in i['series']:
                if s['release'] == release:
                    values = [g['code'], g['title'],
                              t['code'], t['description'], 
                              i['code'], i['description'], i['tier'], 
                              s['code'], s['description']]
                    
                    keys_and_values = zip(keys, values)
                    serie_dic = {}
                    for key, value in keys_and_values:
                        serie_dic[key] = value
                    series_list.append(serie_dic)
                        
# Example:  series_list = 
# [{
#    'goalCode': '1',
#    'goalDesc': 'End poverty in all its forms everywhere',
#    'targetCode': '1.1',
#    'targetDesc': 'By 2030, eradicate extreme poverty for all people everywhere, currently measured as people living on less than $1.25 a day',
#    'indicatorCode': '1.1.1',
#    'indicatorDesc': 'Proportion of population below the international poverty line, by sex, age, employment status and geographical location (urban/rural)',
#    'indicatorTier': '1',
#    'seriesCode': 'SI_POV_DAY1',
#    'seriesDesc': 'Proportion of population below international poverty line (%)'
#}, ...]

#=================================================
# CREATE COUNTRY PROFILES
#=================================================
                  
count_country = 0

for this_country in countryArray:
   # this_country = countryArray[51]   
    count_country += 1
            
    country_profile = {}
    country_profile['release'] = release 

    country_code = str(this_country['geoAreaCode'])
    country_name = this_country['geoAreaName']
    
    country_profile['country_code'] = country_code
    country_profile['country_name'] = country_name
    
    print("Building country profile for ", country_name, " - (", count_country, ")")
    
    country_profile['facts'] = []
    
    count_fact = 0
    
    for this_fact in fact_builder:
    #this_fact = fact_builder[1]
        
        count_fact += 1
        
        if this_fact['Profile.Series'] != '1':
            continue
            
        fact = {}
                
        goal = this_fact['Goal.ID']
        series = this_fact['SeriesCode']
        
        print("Adding fact - (", count_fact, ") for series ", series, "of goal ", goal)
                
        #----------------------------------------------------------------
        # Get descriptive information to accompany this fact 
        #----------------------------------------------------------------

        for s in series_list:
            if (s['goalCode']==goal and s['seriesCode'] == series):
                slice_description = s
                continue
        #print(slice_description)

        for i in slice_description:
            fact[i] = slice_description[i]

        #-----------------------------------------------------------
        # Select dimensions values that are applicable for this fact
        #-----------------------------------------------------------

        slice_dimensions = {d: this_fact[d] for d in this_fact.keys() &
                            {'Age', 
                             'Location', 
                             'Sex', 
                             'Bounds', 
                             'Education level', 
                             'Type of product', 
                             'Type of mobile technology', 
                             'Type of speed'}}

        slice_dimensions = dict((k, v) for k, v in slice_dimensions.items() if v != '')

        #print(slice_dimensions)
        
        fact['slice_dimensions'] = slice_dimensions

        #---------------------------------------------------------
        # Build API call to collect the data for this fact
        #--------------------------------------------------------

        baseURL = 'https://unstats.un.org/SDGAPI/v1/sdg/Series/'

        if(len(slice_dimensions)>0):

            dimensions = ""
            first = True
            for d in slice_dimensions:
                dimension_name = d
                dimension_value = slice_dimensions[d]
                dimension_string = '{name:"'+ dimension_name +'",values:["'+ dimension_value + '"]}'
                if first:
                    dimensions = dimension_string
                    first = False
                else:
                    dimensions = dimensions + "," + dimension_string

            dimensions = "[" + dimensions + "]"

            dimensions = urllib.parse.quote(dimensions, safe='')

            url = baseURL + series + "/GeoArea/" + country_code + "/DataSlice?dimensions=" + dimensions + ""

        else:

            url = baseURL + series + "/GeoArea/" + country_code + "/DataSlice"

        #----------------------------------------------------------------
        # Make a GET request using the http object that you just created 
        #----------------------------------------------------------------

        response = http.request('GET', url)

        data = json.loads(response.data.decode('UTF-8'))
        data = data['dimensions']
        #print("len(data) = " , len(data))
        
        # Add data to 
        fact['data'] = data

        #----------------------------------------------------------------
        # Main fact calculation 
        #----------------------------------------------------------------
        
        #print(this_fact_dic)
        
        facts = []
        values = []
        years = []
        values_is_censored = []
        values_numeric_part = []
        values_alpha_part = []
        
        n = None      # number of observations available
        y_min = None    # first year available
        y_max = None    # most recent year available

        value_y_min = None   # data value in the first year available
        value_y_max = None   # data value in the most recent year available

        value_y_min_num = None   # data value in the first year available
        value_y_max_num = None   # data value in the most recent year available


        value_median = None
        dif_first_last = None
        value_y_max_is_censored = None
        
        prog = ""
        prog_10 = ""
        prog_12 = ""
        prog_15 = ""
        prog_mmr_min = ""
        prog_mmr_max = ""

        fact_text = ""
        
        #---------------------------------------
        # Eliminate non-numeric values (e.g. NA)
        #--------------------------------------
        
        def hasNumbers(inputString):
            return any(x.isdigit() for x in inputString)

        for d in data[:]:
            if not hasNumbers(d['value']):
                data.remove(d)
            
        #--------------------------------------    
            
        if len(data) > 0:
            
            for d in data:
                d['year'] = d.pop('timePeriodStart')
                del(d['Reporting Type'])

            numeric_part = re.compile(r'[^\d.\-]+')
            alpha_part = re.compile(r'[\d.\-]+')
            
           

            for d in data:
                values.append(d['value'])
                years.append(d['year'])
                if d['value'].isalpha():
                    values_is_censored.append(True)
                else:
                    values_is_censored.append(False)
                
                values_numeric_part.append(float(numeric_part.sub('', d['value'])))
                    
                values_alpha_part.append(alpha_part.sub('', d['value']))


            for i in range(len(values)):
                values[i] = values[i].replace("<", "less than ")
                values[i] = values[i].replace(">", "more than ")

                
            
            
            for i in range(len(values_numeric_part)):
                if values_numeric_part[i] is not None:
                    if values_numeric_part[i] <0.99 :
                        values_numeric_part[i] = round_KFM(values_numeric_part[i],2)
                    if values_numeric_part[i] >= 0.99 and values_numeric_part[i] <= 10:
                        values_numeric_part[i] = round_KFM(values_numeric_part[i],1)
                    if values_numeric_part[i] >10 :
                        values_numeric_part[i] = round_KFM(values_numeric_part[i],0)




            #print(values)
            #print(years)
            #print(values_is_censored)
            #print(values_numeric_part)
            #print(values_alpha_part)



            #===============================================================================


            #----------------------------------------------------------------
            # Initial auxiliary variables
            #----------------------------------------------------------------


            n = len(data)      # number of observations available
            y_min = min(years)    # first year available
            y_max = max(years)    # most recent year available

            value_y_min = values[years.index(min(years))]   # data value in the first year available
            value_y_max = values[years.index(max(years))]   # data value in the most recent year available

            value_y_min_num = values_numeric_part[years.index(min(years))]   # data value in the first year available
            value_y_max_num = values_numeric_part[years.index(max(years))]   # data value in the most recent year available


            value_median = statistics.median(values_numeric_part)
            dif_first_last = abs(values_numeric_part[years.index(min(years))] - values_numeric_part[years.index(max(years))])

            value_y_max_is_censored = values_is_censored[years.index(max(years))]


            #print(value_y_min)
            #print(value_y_max)
            #print(value_median)
            #print(dif_first_last)


            #--------------------------------------------------------
            #Information about status of progress: decline/increase?
            #---------------------------------------------------------

            if (value_y_min_num > value_y_max_num):
                prog = this_fact['Down'] 
                # Example: "declined from", "down from"
            elif (value_y_min_num < value_y_max_num):
                prog = this_fact['Up']
                # Example: "increased from", "up from"
            else:
                prog = ""

            #print(prog)

            #--------
            # prog.15
            #--------
            if value_y_min_num < 0.01:
                 prog_15 = "nearly no coverage"
            else:
                prog_15 = str(value_y_min_num) + this_fact['unit1']

            #--------
            # prog.10
            #--------

            if value_y_max_num < 10:
                prog_10 = this_fact['Down']
            else:
                prog_10 = this_fact['Up']

            #--------
            # prog.12
            #--------

            if value_y_max_num > 0:
                prog_12 = this_fact['Up'] 
            else:
                prog_12 = this_fact['Down']


            #-------------
            # prog_mmr_min
            #-------------
            if value_y_min_num > 1: 
                prog_mmr_min = "deaths"
            else:
                prog_mmr_min = "death"

            #-------------
            # prog_mmr_max
            #-------------
            if value_y_max_num > 1: 
                prog_mmr_max = "deaths" 
            else:
                prog_mmr_max = "death"

            #print("min = ",value_y_min_num)
            #print("max = ",value_y_max_num)
            #print("prog = ",prog)
            #print(prog_15)
            #print(prog_10)
            #print(prog_12)
            #print(prog_mmr_min)
            #print(prog_mmr_max)


            #--------------------------------------------------------------------

            fact_text = ""

            condition1 = dif_first_last >= 0.05 * abs(value_y_max_num) 
            condition2 = not value_y_max_is_censored
            condition3 = value_y_max_num >= .25*value_median
            condition4 = int(y_min) < 2010
            condition5 = n > 1

            conditions = condition1 and condition2 and condition3 and condition4 and condition5

            #print("condition1 = ", condition1)
            #print("condition2 = ", condition2)
            #print("condition3 = ", condition3)
            #print("condition4 = ", condition4)
            #print("condition5 = ", condition5)
            #print("conditions = ", conditions)


            if this_fact['Text.type'] =='1':
                fact_title = slice_description['seriesDesc']
                if conditions:
                    fact_text = this_fact['DA3.1'] + prog + " <strong>" + str(value_y_min_num) + this_fact['unit1']  + "</strong>" + " in " +  "<strong>" + str(y_min) + "</strong>" + " to " + "<strong>" + str(value_y_max_num) + this_fact['unit1']+ "</strong> " +  " in " +  " <strong>" + str(y_max)  + "</strong>" + "."
                    fact_values = [ str(value_y_min_num) + this_fact['unit1'], str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_min), str(y_max)]
                else:
                    fact_text = this_fact['DA2.1'] +  "<strong>" + str(value_y_max_num)  +  this_fact['unit1'] + "</strong>"  + " in " + "<strong>" + str(y_max)  + "</strong>" + '.'
                    fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_max)]
                
            elif this_fact['Text.type'] == '2':
                fact_title = slice_description['seriesDesc']
                fact_text = "In " +  "<strong>" + y_max  + "</strong>" + ", " +  "<strong>" + str(value_y_max_num) + this_fact['unit1'] + "</strong> " + this_fact['DA2.1']
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]
                
            elif this_fact['Text.type'] == '3':
                fact_title = slice_description['seriesDesc']
                fact_text = "In " +  "<strong> " + y_max +  "</strong> " + ", " + this_fact['DA2.1'] +   "<strong> " + str(value_y_max_num) + this_fact['unit1'] +  "</strong> " + this_fact['DA2.2']
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]
                
            elif this_fact['Text.type'] == '4':
                fact_title = slice_description['seriesDesc']
                fact_text = this_fact['DA2.1']+  "<strong>"  + str(value_y_max_num) +  "</strong> " + " in " + "<strong> " + y_max +  "</strong> " + ", meaning "+  "<strong> "  + str(float(value_y_max_num) * 100) +  "</strong> " + this_fact['DA2.2'] + "." 
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '7':
                fact_title = slice_description['seriesDesc']
                fact_text = this_fact['DA2.1'] +  "<strong> " + str(value_y_max_num) + this_fact['unit1']+  "</strong> "  + " in "+  "<strong> "  + str(y_max)+  "</strong> "  + "."
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '8':
                fact_title = slice_description['seriesDesc']
                fact_text = "In "+  "<strong> "  + y_max+  "</strong> "  + ", " +  "<strong> " + str(value_y_max_num)  + this_fact['unit1'] +  "</strong> "+ this_fact['DA2.1'] + "."
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '9':
                fact_title = slice_description['seriesDesc']
                if conditions:
                    fact_text = "In "+  "<strong> " + y_max +  "</strong> "+ ", " + this_fact['DA2.1'] +  "<strong> "+ str(value_y_max_num) + this_fact['unit1']+  "</strong> " + ", " + prog +  "<strong> "+ str(value_y_min_num) +  "</strong> " + this_fact['unit2'] + " in "+  "<strong> " + y_min +  "</strong> "
                    fact_values = [ str(value_y_min_num) + this_fact['unit1'], str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_min), str(y_max)]
                else:
                    fact_text = "In "+  "<strong> " + y_max+  "</strong> " + ", " + this_fact['DA2.1'] +  "<strong> "+ str(value_y_max_num) + this_fact['unit1']+  "</strong> " + "."
                    fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '10':
                fact_title = slice_description['seriesDesc']
                fact_text =  "In " +  "<strong> "+ y_max +  "</strong> "+ ", " +  this_fact['DA2.1'] +  "<strong> "+ str(value_y_max_num) + this_fact['unit1']+  "</strong> " + ". " + prog_10 
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '11':
                fact_title = slice_description['seriesDesc']
                fact_text = "In "+  "<strong> " + y_max+  "</strong> " + ", " +  this_fact['DA2.1']+  "<strong> " + str(value_y_max_num) + this_fact['unit1'] +  "</strong> "+ ". "
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '12':
                fact_title = slice_description['seriesDesc']
                fact_text = "As of " +  "<strong> "+ y_max +  "</strong> "+ ", " + country_name + prog_12 + "."
                fact_values = [ str(value_y_max_num)]
                fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '13':
                fact_title = slice_description['seriesDesc']
                fact_text =  "In " +  "<strong> "+ y_max+  "</strong> " + ", " +  this_fact['DA2.1']+  "<strong> " + str(value_y_max_num) + this_fact['unit1'] +  "</strong> "+ this_fact['DA2.2'] + "."
                fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '14':
                fact_title = slice_description['seriesDesc']
                if conditions:
                    fact_text = this_fact['DA3.1'] + prog +   "<strong>" + str(value_y_min_num) + this_fact['unit1']+  "<strong> " + " in " +  "<strong> "+ y_min+  "</strong> " + " to "+  "<strong> " + str(value_y_max_num) + this_fact['unit1'] +  "</strong> "+ " in " +  "<strong> " + y_max+  "</strong> " + "."
                    fact_values = [ str(value_y_min_num) + this_fact['unit1'], str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_min), str(y_max)]
                else:
                    fact_text = this_fact['DA2.1'] +  "<strong> "+ str(value_y_max_num)+  "</strong> " + prog_mmr_max + this_fact['unit1'] + " in "+  "<strong> " + str(y_max) +  "</strong> "+ "."
                    fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_max)]

            elif this_fact['Text.type'] == '15':
                fact_title = slice_description['seriesDesc']
                if conditions:
                    fact_text =  "In "+  "<strong> " + y_max +  "</strong> "+ ", " +  this_fact['DA2.1'] +  "<strong> "+ str(value_y_max_num) +  "</strong> "+ this_fact['unit1'] + "," + prog + prog_15 + " in "+  "<strong> " + y_min +  "</strong> "+ "."
                    fact_values = [ str(value_y_min_num) + this_fact['unit1'], str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_min), str(y_max)]
                else:
                    fact_text =  "In "+  "<strong> " + y_max+  "<strong> " + ", " +  this_fact['DA2.1'] +  "<strong> "+ str(value_y_max_num)+  "</strong> " + this_fact['unit1'] + "."
                    fact_values = [ str(value_y_max_num)+ this_fact['unit1']]
                    fact_years =  [ str(y_max)]


            fact['text_type'] = this_fact['Text.type']
            fact['fact_title'] = fact_title
            fact['fact_text'] = fact_text
            fact['fact_values'] = fact_values
            fact['fact_years'] = fact_years
            fact['data_years'] = years
            fact['data_values'] = values
            fact['data_is_censored'] = values_is_censored
            fact['data_numeric_part'] = values_numeric_part

            #=======================  
            facts.append(fact)

        #=======================  
        country_profile['facts'].append(facts)

    #=======================
    
    #with open('resolutions.json', 'w') as outfile:
    with open("country profile " + country_code + " " + country_name, 'w') as outfile:
        json.dump(country_profile, outfile, indent=4 )    
    
    #with open('resolutions.json', 'w') as outfile:



