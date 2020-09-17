# iremus 2020
# Project auterp rdf
# python functions for the project
# Cedric
# 07/09/2020

## setting work environment
# loading libraries
import os
import json
import pandas as pd
import urllib.request
import gzip
from geopy.geocoders import Nominatim
from openpyxl import load_workbook
import random
from rdflib import Graph, RDF, URIRef, Literal
from rdflib.namespace import SKOS, DC, RDFS
import uuid
from rdflib.namespace import Namespace

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/GIT")

def DownloadFileGz(url,file_path):
    """
    parameters: url of the file to download, file path where file will be stored
    fun: download a Gz file and unzip it
    """
    
    print("Downloading the json file...")
    urllib.request.urlretrieve(url, file_path)
    print("Download complete")
    
    # unzipping the file
    js_unzipped = gzip.GzipFile(file_path, 'rb')
    s = js_unzipped.read()
    js_unzipped.close()
    
    # saving the file
    output = open("input/iconclass_20200710_skos_jsonld.ndjson", 'wb')
    output.write(s)
    output.close()
    
    # deleting compressed file
    os.remove(file_path)

    return None


def ExtractingFromJson(path, key, path_output):
    """
    parameters: path of the json, json key where the data is stored, path 
                output for the csv
    fun: extract data from a json and outputs a csv

    """

    ## extracting codes from the json
    # opening and loading the file
    with open(path, "r") as jsonline: 
        Lines = jsonline.readlines()
    
    # creating an empty list for the iconclass codes
    list_codes = []
    
    # extracting the codes and putting into the list codes
    # some lines are not json so they are removed with an exception
    print("""Extracting codes from the json file. Non-readable lines are
          printed.""")
    for line in Lines:
        try:
            data = json.loads(line)
            code = data[key]
            list_codes.append(code)
        except:
            # checking for errors
            print(line)
            
    # creating a pd dataframe before exporting
    dict_codes = {"codes" : list_codes}
    df = pd.DataFrame(dict_codes)
    
    # exporting the result as an excel
    df.to_csv(path_output)
    
    return list_codes


def ExtractCoordinates(names, exception):
    """
    Parameters
    ----------
    names : list
        list of cities as strings.
    exception : str
        exception in the string names.

    Returns
    -------
    coords : list
        list of coordinates.
    """
    
    # creating an empty list for the cities strings
    cities = []
    
    # extracting city names
    for location in names:
        try:
            city = location[:location.index(",")]
            cities.append(city)
        except:
            if location == exception:
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
    
    return coords
    
    
def SaveExcel(list_sheets, df, path_excel):
    """
    Parameters
    ----------
    list_sheets : list
        list of the different excel sheets to update.
    df : panda dataframe
        updated data to be saved in the excel.
    path_excel : str
        path where the excel is stored.

    Returns
    -------
    None.
    """
    
    for  sheet_nam in list_sheets:
    
        # loading the sheet
        sheet = df[sheet_nam]
        
        # loading the excel
        book = load_workbook(path_excel)
        
        # creating an excel sheet
        writer = pd.ExcelWriter(path_excel, engine = 'openpyxl')
        writer.book = book
        
        # remove the previous excel sheet and saving the file
        sheet_rem = book.get_sheet_by_name(sheet_nam)
        book.remove_sheet(sheet_rem)
        book.save(path_excel)
        
        # putting our new sheet into the excel
        sheet.to_excel(writer, index=False, sheet_name=sheet_nam, startrow=0)
        
        # saving the file
        writer.save()
    
    return None


def ExtractUriCode(path_excel, sheets, uris_label, codes_label):
    """
    parameters: path_excel string of our file, sheets list of sheet names as
                string, uris_label name of the column used for uris as a string,
                codes_label name of the column used for codes as a string
    fun: returns a dictionary with as keys the codes and as values the uris
    """
    
    dict_uris_codes = {}

    # extracting our themes in a list
    excel_df = pd.read_excel(path_excel, sheet_name=sheets)
    
    # filling the dictionary
    for sheet_name in sheets:
        
        # loading the sheet
        sheet = excel_df[sheet_name]
        
        # extracting nids and uris
        uris = sheet[uris_label]
        codes = sheet[codes_label]
    
        # adding them to the dictionary
        for uri, code in zip(uris, codes):
            dict_uris_codes[code] = uri
    
    return dict_uris_codes
    

def GenerateTtlThesauri(thes_list, taxo):
    """
    parameters: thes_list a list of the excel sheets in string, taxo a dictionary
                of dataframes
    fun: generates a turtle rdf for each dataframe and returns saves generated
         urls in the dataframes, returns the updated dictionary
    """
    
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
    
    return taxo


def generate_rdf_url(rand_nb, str_url):
    """

    Parameters
    ----------
    rand_nb : random.Random
        random number generator.
    str_url : str
        string of the url before the uuid.

    Returns
    -------
    URIRef url object

    """
    
    # generating the url
    uid = uuid.UUID(int=rand_nb.getrandbits(128))
    
    return URIRef(str_url + str(uid))


def GenerateTtlPlaces(taxo):
    """
    parameters: a dictionary containing all our dataframes (excel sheets)
    fun: creates a specific ttl for places, that adds cidoc properties 
         and instances. returns the updated dictionary
    """
    
    # loading the sheet with places
    sheet = taxo["Lieu de conservation"]
    
    # generating cidoc crm namespace
    crm = Namespace('https//cidoc-crm.org/cirdoc-crm/')
    
    # we load a number used for uuri generation
    nb_r = 10 ** 6
    rand_nb = random.Random()
    
    # generating the uri for the scheme
    rand_nb.seed(nb_r)
    uid = uuid.UUID(int=rand_nb.getrandbits(128))
    
    # incrementing the index for the thesaurus uris
    nb_r += 1
    
    # creating the UURI for the conceptscheme
    scheme_uuri = URIRef("http://data-iremus.huma-num.fr/id/" + str(uid))
    
    # creating the graph object
    g = Graph()
    
    # generate prefixes
    g.bind("skos", SKOS)
    g.bind("dc", DC)
    g.bind("crm", crm)
    
    ## creating the triple for the concept scheme
    # adding triples
    g.add((scheme_uuri, RDF.type, SKOS.ConceptScheme))
    g.add((scheme_uuri, DC.title, Literal("Lieu de conservation", lang="fr")))
    
    # list of urls
    urls = []
    
    # string used to generate urls
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    ## generate the E53 place for the city (exception if city is missing)
    # creating a dictionary and a list to store names and urls
    cities_urls = {}
    cities_names = []
    
    for label, id_uuri in zip(sheet["name"], sheet["uuid"]):
        try:
            city_name = label[:label.index(",")]
            cities_names.append(city_name)
            
        except:
            None
        
    # remove duplicates
    cities_names = list(dict.fromkeys(cities_names))
    
    # generate the E53 place for the city
    for name_c in cities_names:
        # generating url
        rand_nb.seed(nb_r)
        url_city = generate_rdf_url(rand_nb, str_url)
        g.add((url_city, RDF.type, crm.E53_place))
        g.add((url_city, RDFS.label, Literal(name_c)))
        
        # incrementing the seed for random number generation
        nb_r += 1
        
        # storing the url
        cities_urls[name_c] = url_city
        
    ## generate the E53 place for the musem
    # creating a dictionary and a list to store names and urls
    museums_urls = {}
    museums_names = []
    
    for label, id_uuri in zip(sheet["name"], sheet["uuid"]):
        try:
            musem_name = label[label.index(","):][2:]
            museums_names.append(musem_name)
            
        except:
            museums_names.append(label)
    
    # remove duplicates
    museums_names = list(dict.fromkeys(museums_names))
            
    # generate the E41 appellation for the museums
    for name_m in museums_names:
        # generating url
        rand_nb.seed(nb_r)
        url_museum = generate_rdf_url(rand_nb, str_url)
        g.add((url_museum, RDF.type, crm.E41_Appellation))
        g.add((url_museum, RDFS.label, Literal(name_m)))
        
        # incrementing the seed for random number generation
        nb_r += 1
        
        # storing the url
        museums_urls[name_m] = url_museum
    
    for label, id_uuri in zip(sheet["name"], sheet["uuid"]):
        
        # generating the uri
        our_url = URIRef("http://data-iremus.huma-num.fr/id/" + str(id_uuri))
        
        # storing the uri in a list to add it to the conceptscheme
        urls.append(our_url)
        
        # adding the triples
        g.add((our_url, RDF.type, SKOS.Concept))
        g.add((our_url, SKOS.prefLabel, Literal(label, lang="fr")))
        g.add((our_url, SKOS.inScheme, scheme_uuri))
        
        ## adding the CIDOC triples
        # creating the instance place
        g.add((our_url, RDF.type, crm.E53_place))
        
        # generate the E53 place for the city (exception if city is missing)
        try:
            city_name = label[:label.index(",")]
            g.add((our_url, crm.p89_falls_within, cities_urls[city_name]))
        except:
            None
        
        # generate the appelation (exception if the city is missing)
        try:
            musem_name = label[label.index(","):][2:]
            g.add((our_url, crm.p1_is_identified_by,
                   museums_urls[musem_name]))
        except:
            g.add((our_url, crm.p1_is_identified_by,
                   museums_urls[label]))
    
    # adding the uuri to the conceptscheme
    for ur in urls:
        g.add((scheme_uuri, SKOS.hasTopConcept, ur))
    
    # outputting the rdfs as a turtle file
    g.serialize(destination='output/Lieu de conservation.ttl', format='turtle')
    
    # adding the uuris to the pd dataframe
    sheet["urls"] = urls
    
    # updating the data
    taxo["Lieu de conservation"] = sheet
    
    return taxo