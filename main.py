# iremus 2020
# Project auterp rdf
# main python script for the project
# Cedric
# 03/09/2020

## setting work environment
# loading libraries
import os
import pandas as pd
import shutil

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/GIT")

# importing our functions
import python.functions as fun

# copying our original excel sheet in the output
shutil.copyfile('input/taxonomies.xlsx', 'output/taxonomies_modified.xlsx')

### extracting and saving iconclass codes
print(
"""
We download the json containing all skos codes of iconclass from
iconclass.org, and we save the codes in a csv
"""
)

## downloading the json file with all iconclass codes
url = 'http://iconclass.org/data/iconclass_20200710_skos_jsonld.ndjson.gz'
json_path_comp = "input/iconclass_20200710_skos_jsonld.ndjson.gz"
fun.DownloadFileGz(url, json_path_comp)

## extracting codes from the json and storing it in a list
path_json = "input/iconclass_20200710_skos_jsonld.ndjson"
key = "skos:notation"
file_output = "output/icon_class_codes.csv"
iconclasses_list = fun.ExtractingFromJson(path_json, key, file_output)

# deleting the json file
os.remove("input/iconclass_20200710_skos_jsonld.ndjson")

### finding non iconclass ids
print(
"""
We compare the iconclass codes with the one in the input files. for the
new ones we will create a new colums where modification is indicated.
The result is saved in a dictionary of panda dataframes
"""
)

# creating a list with all our thesaurus
thes_list = ['spécialité',
             'Période',
             'École',
             'Domaine',
             'Lieu de conservation',
             'Thème',
             'Instrument de musique',
             'Notation musicale',
             'Chant',
             'Support',
             'Type oeuvre']

# extracting our themes in a list
taxo = pd.read_excel("input/taxonomies.xlsx", sheet_name=thes_list)
themes = taxo["Thème"]
data = list(themes["name"])

# creating an empty list where we store our codes
codes = []

# extracting our codes
for theme in data:
    try:
        code = theme[:theme.index("-")][:-1]
        if code[0].isdigit():
            codes.append(code)
        
        else:
            codes.append(None)
    except:
        codes.append(None)

# creating a list to know if it is modified or not
modified = []

for code in codes:
    if code == None:
        modified.append(None)
        
    elif code in iconclasses_list:
        modified.append("no")
        
    else:
        modified.append("yes")
        
# updating the df of our taxonomy
taxo["Thème"]["modification"] = modified

### creating rdfs from our thesaurus
print(
"""
We extract our uuids and create new ones for each thesaurus, and then generate
our turtle rdfs. We then build our urls and store them in the dataframe. We 
"""
)

## looping throught the different excel sheets and generating a turtle file for each
taxo = fun.GenerateTtlThesauri(thes_list, taxo)
taxo = fun.GenerateTtlPlaces(taxo)
    
### calculating coordinates
print(
"""
We extract the citys name from 'lieu de conservation' and load its corresponding
coordinates in WGS84 (coordinate system), then saving it into the dataframe
With a slow connection this might takes some time
"""
)

## extracting cities strings and putting them in a list
# extracting our themes in a list
names = list(taxo["Lieu de conservation"]["name"])

# extracting the coordinates from the list of names and the dataframe
coords = fun.ExtractCoordinates(names, "collection privée")

# saving the coords in our dataframe
taxo["Lieu de conservation"]["coords_wgs84"] = coords

### saving the excel
print(
"""
We save our resulting dataframe in the new excel (taxonomies_modified.xlsx)
"""
)

# saving the excel
fun.SaveExcel(thes_list, taxo, "output/taxonomies_modified.xlsx")


#### working on euterp_data
print(
"""
We now start to work on the euterpe_data
"""
)

## loading our dataframe
# copying our original excel sheet in the output
shutil.copyfile('input/euterpe_data.xlsx', 'output/euterpe_data_modified.xlsx')

# list of the sheets
eut_sheets = ['1_auteurs',
             '4_euterpe_images',
             '5_oeuvres_lyriques',
             '3_euterpe_biblio',
             '6_auteurs_bibli_id']

# loading euterp data
eut_data = pd.read_excel("input/euterpe_data.xlsx", sheet_name=eut_sheets)

### transforming nids into urls
print(
"""
We are now going to transform all nids and tids into  uris
this is done in the euterpe data
"""
)

# extracting the nids and tids and their uris into a dictionary
nid_urls = fun.ExtractUriCode("input/euterpe_data.xlsx", eut_sheets, "uri", "nid")
tid_urls = fun.ExtractUriCode("output/taxonomies_modified.xlsx", thes_list,
                              "urls", "Unnamed: 0")

# merging the two dictionaries
dict_uris_codes = {**nid_urls, **tid_urls}
    
## transforming nids into uris
# empty list to store unknown nid
unkn_nid = []

# looping through the sheets
for sheet_name in eut_sheets:
    
    # looping through the sheets to get the relevant columns
    cols_id = []
    
    # loading the sheet (thesaurus)
    sheet = eut_data[sheet_name]
    
    # extracting the relevant names (they end by _id)
    for name_col in sheet:
        if "_id" in name_col or "_tid" in name_col and "_url" not in name_col:
            cols_id.append(name_col)
            
    ## replacing the ids by uris
    # through the relevant columns
    for col in cols_id:
        
        # looping through the rows to replace ids by uris
        for i in range(len(sheet[col])):
            try:
                # excluding None values
                if str(sheet[col].iloc[i]) == "nan":
                    continue
                
                # list of the ids of the row
                ids_row = []
                
                # removing potential extra character
                ids_cleaned = sheet[col].iloc[i].split(' 🍄 ')
                
                # converting into int
                ids_cleaned = [int(ident) for ident in ids_cleaned]
                
                # looping into the values to detect exceptions
                for our_id in ids_cleaned:
                    if our_id not in dict_uris_codes.keys():
                        unkn_nid.append(our_id)
                    else:
                        ids_row.append(our_id)
                
                # getting the uris in a list
                row_uris = [dict_uris_codes[int(nid_r)] for nid_r in ids_row]
                
                # replacing the result in the dataframe
                sheet[col].iloc[i] = " , ".join(row_uris)
                
            except:
                try:
                    # in case of individual non-string value we try to add it directly
                    sheet[col].iloc[i] = dict_uris_codes[int(sheet[col].iloc[i])]
                except:
                    # storing nids
                    unkn_nid.append(sheet[col].iloc[i])
    
    # checking unknow ids
    unkn_nid = list(dict.fromkeys(unkn_nid))
    
    # printing total of unknown keys
    print("{} codes are unknown, compared to a total of {} keys".format(len(unkn_nid), len(dict_uris_codes)))
    
    # saving the sheet in our dataframe
    eut_data[sheet_name] = sheet


### saving the excel
print(
"""
We save our resulting dataframe in the new excel euterpe_data_modified.xlsx
"""
)

# saving the result in an excel
fun.SaveExcel(eut_sheets, eut_data, "output/euterpe_data_modified.xlsx")
