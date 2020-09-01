# iremus 2020
# Project auterp rdf
# extract icon class codes
# Cedric
# 31/08/2020

# setting work environment
import os
import json
import pandas as pd

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/GIT")

# loading a test json in data
#with open('test.json') as json_file:
#    data = json.load(json_file)

# extracting the icon class code
#data["skos:notation"]

## trying for the whole json
# opening and loading the file
with open("input/iconclass_20200710_skos_jsonld.json", "r") as jsonline: 
    Lines = jsonline.readlines()

# creating an empty list for the iconclass codes
codes = []

# extracting the codes and putting into the list codes
# some lines are not json so they are removed with an exception
for line in Lines:
    try:
        data = json.loads(line)
        iconclass_code = data["skos:notation"]
        codes.append(iconclass_code)
    except:
        print(line)
        
# creating a pd dataframe before exporting
dict_codes = {"codes" : codes}
df = pd.DataFrame(dict_codes)

# exporting the result as an excel
df.to_csv("output/icon_class_codes.csv")