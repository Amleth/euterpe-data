# iremus 2020
# Project auterp rdf
# this script adds uris in the input file, to keep the data stable 
# it is kept outside of the main script
# this script has already been run and shouldn't be run again
# update 16/09/2020
# to facilitate the rdf generation process, we now generate one url per column
# again, the script has been ran only once
# Cedric
# 03/09/2020

import os
import pandas as pd
import uuid
import random
from openpyxl import load_workbook
import shutil

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/GIT")

#### working on euterp_data
"""
We now start to work on the euterpe_data
"""

## loading our dataframe
# copying our original excel sheet in the output
shutil.copyfile('input/euterpe_data.xlsx', 'output/euterpe_data_modified.xlsx')

# list of the sheets
eut_sheets = ['1_auteurs',
             '4_euterpe_images',
             '5_oeuvres_lyriques',
             '3_euterpe_biblio',
             '6_auteurs_bibli_id']

# extracting our themes in a list
eut_data = pd.read_excel("input/euterpe_data.xlsx", sheet_name=eut_sheets)

### transforming nids into urls
"""
We are now going to generate uris for our objects and transform all nids into these uris
this is done in the euterpe data
"""

## generating uris and storing them in the dataframe
# index for random uri generation
i = 100

# creating a distionary to store all the nids and their corresponding uris
nid_urls = {}

for sheet_name in eut_sheets:
    
    # empty list to store the uris
    uris = []
    
    # loading the sheet
    sheet = eut_data[sheet_name]
    
    # loading dictionary to store columns urls
    urls_col = {}
    
    # we generate lists in the dictionary
    for col in sheet.keys():
        urls_col[col] = []
    
    # generating an uri for every row of the sheet
    for nid in sheet["nid"]:
        
        rd = random.Random()
        rd.seed(i)
        uid = uuid.UUID(int=rd.getrandbits(128))
        uri = "http://data-iremus.huma-num.fr/id/" + str(uid)
        uris.append(uri)
        
        # storing nid and url in the dictionary
        nid_urls[nid] = uri
        
        # incrementing the index
        i += 1
        
        """
        We now generate urls for every column, this is done to facilitate later
        steps for our turtle rdf generation
        
        """
        
    
        ## generating uris per column for future rdf
        for col in sheet.keys():
            
            rd = random.Random()
            rd.seed(i)
            uid = uuid.UUID(int=rd.getrandbits(128))
            uri = "http://data-iremus.huma-num.fr/id/" + str(uid)
            
            # storing into the dictionary
            urls_col[col].append(uri)
            
            # incrementing the index
            i += 1
    
    # adding the uris to our dataframe
    eut_data[sheet_name]["uri"] = uris
    
    for col in urls_col:
        eut_data[sheet_name][col + "_url"] = urls_col[col]

### saving the excel
"""
We save our resulting dataframe in the new excel
"""
    
for  sheet_name in eut_sheets:
    
    # loading the sheet
    sheet = eut_data[sheet_name]
    
    # loading the excel
    book = load_workbook("input/euterpe_data.xlsx")
    
    # creating an excel sheet
    writer = pd.ExcelWriter("input/euterpe_data.xlsx", engine = 'openpyxl')
    writer.book = book
    
    # remove the previous excel sheet and saving the file
    sheet_rem = book.get_sheet_by_name(sheet_name)
    book.remove_sheet(sheet_rem)
    book.save('input/euterpe_data.xlsx')
    
    # putting our new sheet into the excel
    sheet.to_excel(writer, index=False, sheet_name=sheet_name, startrow=0)
    
    # saving the file
    writer.save()
    