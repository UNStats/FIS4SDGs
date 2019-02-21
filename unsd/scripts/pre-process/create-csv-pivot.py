import csv
import pandas as pd
import os
import fnmatch
import numpy as np

os.chdir('C:\\Users\\L.GonzalezMorales\\Documents\\GitHub\\FIS4SDGs\\unsd\\data\\csv\\') 

#-------------------------------------------------------
# Get the list of all available csv files in long format
#-------------------------------------------------------

long_files = []

listOfFiles = os.listdir('.')  
pattern = "*_long.csv"  
for entry in listOfFiles:  
    if fnmatch.fnmatch(entry, pattern):
        long_files.append(entry)
        
wide_files = []        
for f in long_files:
    wide_files.append(f.replace("long", "wide"))
    
#-------------------------------------------------------



for i in range(len(long_files)):
    
    f = long_files[i]
    f# = '1.1.1-SI_POV_EMP1_long.csv'
    print("====PIVOTING FILE " + f)

    with open(f) as filename:
        reader = csv.reader(filename)
        data = list(reader)
        
    header = data[0]
    
    if(len(data)>1):
        long_df = pd.DataFrame.from_records(data[1:])
        long_df.columns = header
        long_df.Year = long_df.Year.astype(float).astype(int)
        #-------------------------------------------------------
        # create vector with columns that identify unique slices
        #-------------------------------------------------------
        
        index_c = header
        # Remove values that will be pivoted:
        index_c.remove('Year')
        index_c.remove('Value')
        index_c.remove('Nature_Code')
        index_c.remove('Source')
        index_c.remove('Footnotes')
        index_c.remove('TimeDetail')
        # Drop nature description and value type:
        index_c.remove('Nature_Desc')
        index_c.remove('ValueType')
        # What remains is the key that identifies unique "sclices" in the pivot table
        
        #--------------------------------------------------------
        # Select the most recent observatoin available for each
        # slice
        #--------------------------------------------------------
        
        idx = long_df.groupby(index_c)['Year'].transform(max) == long_df['Year']

        latest_df = long_df[idx]
        
        latest_df.rename(columns={'Year': 'Latest_Year', 'Value': 'Latest_Value'}, inplace=True)
    
        #-------------------------------------------------------
        # Create pivot table
        #-------------------------------------------------------
        
        pivot_table = pd.pivot_table(long_df,
                                     index=index_c,
                                     columns = ['Year'],
                                     values = ['Value','Nature_Code', 'Source', 'Footnotes', 'TimeDetail'],
                                     aggfunc = lambda x: ''.join(str(v) for v in x))
        
        pivot_table = pivot_table.replace(np.nan, '', regex=True)
        #------------------------------------------------------
        # Define new column headings (since this is multi-index)
        #------------------------------------------------------
        
        new_header = index_c[:] 
        
        header_elements = pivot_table.columns
        for c in header_elements:
            new_header.append(c[0]+"_"+ str(c[1]))
        
        
        pivot_table = pivot_table.reset_index()
        
        pivot_table.columns = [''.join(str(col)).strip() for col in pivot_table.columns.values]
        
        pivot_table.columns = new_header
        
        #-------------------------------------------------------
        # Add latest year columns to pivot table
        #-------------------------------------------------------
        
        
        test_merge = pd.merge(pivot_table, latest_df[index_c +['Latest_Year','Latest_Value']], how='outer', on=index_c)
             
        export_csv = test_merge.to_csv (wide_files[i], index = None, header=True) #Don't forget to add '.csv' at the end of the path
   
        #------------------------------------------------------
        
    
