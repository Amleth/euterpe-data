# iremus 2020
# Project auterp rdf
# main python script for the project
# Cedric
# 03/09/2020

## setting work environment
# loading libraries
import os
import json
import pandas as pd
import urllib.request
import gzip
from rdflib import Graph, RDF, URIRef, Literal
from rdflib.namespace import SKOS, DC
import uuid
import random
from openpyxl import load_workbook
import shutil
from geopy.geocoders import Nominatim

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/GIT")

# copying our original excel sheet in the output
shutil.copyfile('input/taxonomies.xlsx', 'output/taxonomies_modified.xlsx')

### extracting and saving iconclass codes
"""
We download the json containing all skos codes of iconclass from
iconclass.org, and we save the codes in a csv
"""
## downloading the json file with all iconclass codes
url = 'http://iconclass.org/data/iconclass_20200710_skos_jsonld.ndjson.gz'
json_path_comp = "input/iconclass_20200710_skos_jsonld.ndjson.gz"
urllib.request.urlretrieve(url, json_path_comp)

# unzipping the file
js_unzipped = gzip.GzipFile(json_path_comp, 'rb')
s = js_unzipped.read()
js_unzipped.close()

# saving the file
output = open("input/iconclass_20200710_skos_jsonld.ndjson", 'wb')
output.write(s)
output.close()

# deleting compressed file
os.remove(json_path_comp)

## extracting codes from the json
# opening and loading the file
with open("input/iconclass_20200710_skos_jsonld.ndjson", "r") as jsonline: 
    Lines = jsonline.readlines()
    
# creating an empty list for the iconclass codes
iconclasses_list = []

# extracting the codes and putting into the list codes
# some lines are not json so they are removed with an exception
for line in Lines:
    try:
        data = json.loads(line)
        iconclass_code = data["skos:notation"]
        iconclasses_list.append(iconclass_code)
    except:
        # checking for errors
        print(line)
        
# creating a pd dataframe before exporting
dict_codes = {"codes" : iconclasses_list}
df = pd.DataFrame(dict_codes)

# exporting the result as an excel
df.to_csv("output/icon_class_codes.csv")

# deleting the json file
os.remove("input/iconclass_20200710_skos_jsonld.ndjson")

### finding non iconclass ids
"""
We compare the iconclass codes with the one in the input files. for the
new ones we will create a new colums where modification is indicated.
The result is saved in a dictionary of panda dataframes
"""
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
"""
We extract our uuids and create new ones for each thesaurus. We then build our
urls and store them in the dataframe
"""

## looping throught the different excel sheets and generating a ttl for each
# creating our index to generate our random uuids
i = 0

for thes in thes_list:
    
    # loading the sheet (thesaurus)
    sheet = taxo[thes]
    
    # generating the uri for the scheme
    rd = random.Random()
    rd.seed(i)
    uid = uuid.UUID(int=rd.getrandbits(128))
    
    # incrementing the index for the thesaurus uris
    i += 1
    
    # creating the UURI for the conceptscheme
    scheme_uuri = URIRef("http://data-iremus.huma-num.fr/id/" + str(uid))
    
    ## making triples from the sheet
    rd = random.Random()
    
    # creating the graph object
    g = Graph()
    
    # generate prefixes
    g.bind("skos", SKOS)
    g.bind("dc", DC)
    
    ## creating the triple for the concept scheme
    # adding triples
    g.add((scheme_uuri, RDF.type, SKOS.ConceptScheme))
    g.add((scheme_uuri, DC.title, Literal(thes, lang="fr")))
    
    # list of urls
    urls = []
    
    for label, id_uuri in zip(sheet["name"], sheet["uuid"]):
        
        # generating the uri
        our_url = URIRef("http://data-iremus.huma-num.fr/id/" + str(id_uuri))
        
        # storing the uri in a list to add it to the conceptscheme
        urls.append(our_url)
        
        # adding the triples
        g.add((our_url, RDF.type, SKOS.Concept))
        g.add((our_url, SKOS.prefLabel, Literal(label, lang="fr")))
        g.add((our_url, SKOS.inScheme, scheme_uuri))
    
    # adding the uuri to the conceptscheme
    for ur in urls:
        g.add((scheme_uuri, SKOS.hasTopConcept, ur))
    
    # vizualizing the result
    #print(g.serialize(format="turtle").decode("utf-8"))
    
    # outputting the rdfs as a turtle file
    g.serialize(destination='output/'+thes+'.ttl', format='turtle')
    
    # adding the uuris to the pd dataframe
    sheet["urls"] = urls
    
    # updating our dataframe
    taxo[thes] = sheet
        
### calculating coordinates
"""
We extract the citys name from 'lieu de conservation' and load its corresponding
coordinates in WGS84 (coordinate system), then saving it into the dataframe
"""

## extracting cities strings and putting them in a list
# extracting our themes in a list
names = list(taxo["Lieu de conservation"]["name"])

# creating an empty list for the cities strings
cities = []

# extracting city names
for location in names:
    try:
        city = location[:location.index(",")]
        cities.append(city)
    except:
        if location == "collection privée":
            cities.append("no location is available")
        else:
            cities.append(location)

## getting the coordinates
# creating geolocator object
geolocator = Nominatim(user_agent="Iremus")

# creating an empty list to store our coordinates
coords = []

# looping through our cities and store their coordinates
for city in cities:
    try:
        location = geolocator.geocode(city)
        coords.append((location.latitude, location.longitude))
    except:
        coords.append(None)

# saving the coords in our dataframe
taxo["Lieu de conservation"]["coords_wgs84"] = coords

### saving the excel
"""
We save our resulting dataframe in the new excel
"""
    
for  thes in thes_list:
    
    # loading the sheet
    sheet = taxo[thes]
    
    # loading the excel
    book = load_workbook("output/taxonomies_modified.xlsx")
    
    # creating an excel sheet
    writer = pd.ExcelWriter("output/taxonomies_modified.xlsx", engine = 'openpyxl')
    writer.book = book
    
    # remove the previous excel sheet and saving the file
    sheet_rem = book.get_sheet_by_name(thes)
    book.remove_sheet(sheet_rem)
    book.save('output/taxonomies_modified.xlsx')
    
    # putting our new sheet into the excel
    sheet.to_excel(writer, index=False, sheet_name=thes, startrow=0)
    
    # saving the file
    writer.save()