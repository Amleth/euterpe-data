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
import numpy as np

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/GIT")

# generating cidoc crm namespace
crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')

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

    
    # creating a dictionary to store the data
    dict_coords = {}
    
    # looping through our cities and store their coordinates
    for city in cities:
        try:
            location = geolocator.geocode(city)
            dict_coords[city] = (location.latitude, location.longitude)
        except:
            None
            
    return dict_coords
    
    
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
    

def GenerateTtlThesauri(thes_list, taxo, i):
    """
    parameters: thes_list a list of the excel sheets in string, taxo a dictionary
                of dataframes, the number to generate uuids
    fun: generates a turtle rdf for each dataframe and returns saves generated
         urls in the dataframes, returns the updated dictionary
    """
    
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
            g.add((our_url, RDF.type, crm.E55_type))
            g.add((our_url, SKOS.prefLabel, Literal(label, lang="fr")))
            g.add((our_url, SKOS.inScheme, scheme_uuri))
        
        # adding the uuri to the conceptscheme
        for ur in urls:
            g.add((scheme_uuri, SKOS.hasTopConcept, ur))
        
        # vizualizing the result
        #print(g.serialize(format="turtle").decode("utf-8"))
        
        # creating a new column to store urls
        sheet["urls"] = urls
        
        # storing the urls in the df
        taxo[thes] = sheet
        
        # outputting the rdfs as a turtle file
        g.serialize(destination='output/'+thes+'.ttl', format='turtle')
        
    return taxo, i


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


def GenerateTtlPlaces(taxo, nb_r, coordinates):
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
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    
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
        nb_r += 1
        
        # generating instance
        g.add((url_city, RDF.type, crm.E53_place))
        g.add((url_city, RDFS.label, Literal(name_c)))
        
        # generating instance for coordinates
        try:
            rand_nb.seed(nb_r)
            url_coord = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_city, crm.p172_contains, url_coord))
            g.add((url_coord, RDFS.label, Literal(coordinates[name_c])))
        except:
            None
        
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
    
    return nb_r


def GenerateTtlSpecialThesauri(taxo, thesau, crm_concept, uuid):
    """
    parameters: a dictionary containing all our dataframes (excel sheets), the 
                name of the thesauri as a string, the cidoc crm concept we 
                want to use as a namespace object, and uuid for the concept
                scheme, and the number for uuri generation
    fun: creates a specific ttl for special thesauri using a different cidoc
         instance.
    """
    
    # loading the sheet with places
    sheet = taxo[thesau]
    
    # creating the UURI for the conceptscheme
    scheme_uuri = URIRef("http://data-iremus.huma-num.fr/" + uuid)
    
    # creating the graph object
    g = Graph()
    
    # generate prefixes
    g.bind("skos", SKOS)
    g.bind("dc", DC)
    g.bind("crm", crm)
    
    ## creating the triple for the concept scheme
    # adding triples
    g.add((scheme_uuri, RDF.type, SKOS.ConceptScheme))
    g.add((scheme_uuri, DC.title, Literal(thesau, lang="fr")))
    
    # create a list to store urls
    urls = []
    
    for label, id_uuri in zip(sheet["name"], sheet["uuid"]):
            
        # generating the uri
        our_url = URIRef("http://data-iremus.huma-num.fr/id/" + str(id_uuri))
        
        # storing the uri in a list to add it to the conceptscheme
        urls.append(our_url)
        
        # adding the triples
        g.add((our_url, RDF.type, SKOS.Concept))
        g.add((our_url, RDF.type, crm_concept))
        g.add((our_url, SKOS.prefLabel, Literal(label, lang="fr")))
        g.add((our_url, SKOS.inScheme, scheme_uuri))
        
        # vizualizing the result
        #print(g.serialize(format="turtle").decode("utf-8"))
    
    # adding the urls as top concepts of the concept scheme
    for ur in urls:
            g.add((scheme_uuri, SKOS.hasTopConcept, ur))
        
    # outputting the rdfs as a turtle file
    g.serialize(destination='output/'+thesau+'.ttl', format='turtle')
    
    
        
    return None


def AddingProductionTid(url_producer, g, nb_r, rand_nb, tid, url_subprod,
                        concept, concepts_urls, eut_auteurs):
    """
    Parameters (in order): url of the authors, graph g, index to generate random number,
                random number generater, tid as a string (field), url of the 
                production associated to the author, type of E13, dictionary
                of our concepts, database of our authors
    Fun: extracts school and period from the authors database to add it to the
         production of the art piece, as an attribute E13

    """
    
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # generating cidoc crm namespace
    crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
    
    # adding the tid
    periods = eut_auteurs[tid].loc[eut_auteurs["uri"]==url_producer].iloc[0]
    if periods is np.nan:
        None
    elif len(periods.split(sep=" , ")) > 1 :
        for one_period in periods.split(sep=" , "):
            rand_nb.seed(nb_r)
            url_attri = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_attri, RDF.type, crm.E13_Attribute))
            g.add((url_attri, crm.p140_assigned_attribute_to, url_subprod))
            g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
            g.add((url_attri, crm.p177_assigned_property_type, concepts_urls[concept] ))
            g.add((url_attri, crm.p141_assigned, URIRef(one_period)))
        
    else:
        rand_nb.seed(nb_r)
        url_attri = generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        g.add((url_attri, RDF.type, crm.E13_Attribute))
        g.add((url_attri, crm.p140_assigned_attribute_to, url_subprod))
        g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
        g.add((url_attri, crm.p177_assigned_property_type, concepts_urls[concept] ))
        g.add((url_attri, crm.p141_assigned, URIRef(periods)))
    
    return g, nb_r

def AddingProducers(urls_producers, g, nb_r, rand_nb, url_prod, concepts_urls, eut_auteurs):
    """
    Parameters (in order): urls of the authors, graphe rdf, index for number
        generation, random generator object, url of the main production event,
        dictionary of our concepts, database of authors
    fun: adds authors as producer of the art work, each author has a distinct
         production event.
    """
    
    # generating the string used for urls
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # generating cidoc crm namespace
    crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
    
    # if the value is empty
    if urls_producers is np.nan:
        None
        
    # in case of several values
    elif len(urls_producers.split(sep=" , ")) > 1 :
        for artist in urls_producers.split(sep=" , "):
            rand_nb.seed(nb_r)
            url_subprod = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_subprod, RDF.type, crm.E12_Production))
            g.add((url_subprod, crm.p9i_forms_part_of, url_prod))
            g.add((url_subprod, crm.p14_carried_out_by, URIRef(artist)))
            g, nb_r = AddingProductionTid(artist, g, nb_r, rand_nb,
                                          "ecole__tid", url_subprod, "url_ecole",
                                          concepts_urls, eut_auteurs)
            g, nb_r = AddingProductionTid(artist, g, nb_r, rand_nb,
                                          "siecle_tid", url_subprod, "url_period",
                                          concepts_urls, eut_auteurs)
    # in case of a unique value
    else:
        rand_nb.seed(nb_r)
        url_subprod = generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        g.add((url_subprod, RDF.type, crm.E12_Production))
        g.add((url_subprod, crm.p9i_forms_part_of, url_prod))
        g.add((url_subprod, crm.p14_carried_out_by, URIRef(urls_producers)))
        g, nb_r = AddingProductionTid(urls_producers, g, nb_r, rand_nb,
                                      "ecole__tid", url_subprod, "url_ecole",
                                      concepts_urls, eut_auteurs)
        g, nb_r = AddingProductionTid(urls_producers, g, nb_r, rand_nb,
                                      "siecle_tid", url_subprod, "url_period",
                                      concepts_urls, eut_auteurs)
    
    return g, nb_r


def AddingCreators(urls_producers, g, nb_r, rand_nb, url_prod, concepts_urls, eut_auteurs):
    """
    Function similar to AddingProducers but uses instance E65_Creation instead
            of Production

    """
    
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # generating cidoc crm namespace
    crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
    
    if urls_producers is np.nan or type(urls_producers) == int:
        None
        
    elif len(urls_producers.split(sep=" , ")) > 1 :
        for artist in urls_producers.split(sep=" , "):
            rand_nb.seed(nb_r)
            url_subprod = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_subprod, RDF.type, crm.E65_Creation))
            g.add((url_subprod, crm.p9i_forms_part_of, url_prod))
            g.add((url_subprod, crm.p94i_was_created_by, URIRef(artist)))
            g, nb_r = AddingProductionTid(artist, g, nb_r, rand_nb,
                                          "ecole__tid", url_subprod, "url_ecole",
                                          concepts_urls, eut_auteurs)
            g, nb_r = AddingProductionTid(artist, g, nb_r, rand_nb,
                                          "siecle_tid", url_subprod, "url_period",
                                          concepts_urls, eut_auteurs)
        
    else:
        rand_nb.seed(nb_r)
        url_subprod = generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        g.add((url_subprod, RDF.type, crm.E12_Production))
        g.add((url_subprod, crm.p9i_forms_part_of, url_prod))
        g.add((url_subprod, crm.p14_carried_out_by, URIRef(urls_producers)))
        g, nb_r = AddingProductionTid(urls_producers, g, nb_r, rand_nb,
                                      "ecole__tid", url_subprod, "url_ecole",
                                      concepts_urls, eut_auteurs)
        g, nb_r = AddingProductionTid(urls_producers, g, nb_r, rand_nb,
                                      "siecle_tid", url_subprod, "url_period",
                                      concepts_urls, eut_auteurs)
    
    return g, nb_r


def AddingAttributedProducer(urls_producers, g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, concept):
    """
    Function similar to Adding Producer but removes the "produced by" property,
    it is used for incertain attribution and hypothesis

    """
    
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # generating cidoc crm namespace
    crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
    
    if urls_producers is np.nan:
        None
    elif len(urls_producers.split(sep=" , ")) > 1 :
        for artist in urls_producers.split(sep=" , "):
            rand_nb.seed(nb_r)
            url_attri = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            rand_nb.seed(nb_r)
            url_subprod = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_attri, RDF.type, crm.E13_Attribute))
            g.add((url_attri, crm.p140_assigned_attribute_to, url_subprod))
            g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
            g.add((url_attri, crm.p177_assigned_property_type, concepts_urls[concept] ))
            g.add((url_attri, crm.p141_assigned, URIRef(artist)))
            g.add((url_subprod, RDF.type, crm.E12_Production))
            g.add((url_subprod, crm.p9i_forms_part_of, url_prod))
            g, nb_r = AddingProductionTid(artist, g, nb_r, rand_nb,
                                          "ecole__tid", url_subprod, "url_ecole",
                                          concepts_urls, eut_auteurs)
            g, nb_r = AddingProductionTid(artist, g, nb_r, rand_nb,
                                          "siecle_tid", url_subprod, "url_period",
                                          concepts_urls, eut_auteurs)
    else:
        rand_nb.seed(nb_r)
        url_attri = generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        rand_nb.seed(nb_r)
        url_subprod = generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        g.add((url_attri, RDF.type, crm.E13_Attribute))
        g.add((url_attri, crm.p140_assigned_attribute_to, url_subprod))
        g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
        g.add((url_attri, crm.p177_assigned_property_type, concepts_urls[concept] ))
        g.add((url_attri, crm.p141_assigned, URIRef(urls_producers)))
        g.add((url_subprod, RDF.type, crm.E12_Production))
        g.add((url_subprod, crm.p9i_forms_part_of, url_prod))
        g, nb_r = AddingProductionTid(urls_producers, g, nb_r, rand_nb,
                                      "ecole__tid", url_subprod, "url_ecole",
                                      concepts_urls, eut_auteurs)
        g, nb_r = AddingProductionTid(urls_producers, g, nb_r, rand_nb,
                                      "siecle_tid", url_subprod, "url_period",
                                      concepts_urls, eut_auteurs)
    
    return g, nb_r


def GeneratingGeneralConcepts(g, crm):
    """
    Generates concepts into a rdf graph and outputs their uri in a dictionary

    """
    
    # creating the dictionary
    concepts_urls = {}
    
    # string used to generate urls
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # generating height triplets
    url_height = URIRef(str_url + "fcdb4c32-7f65-466d-9cfe-251fe0b09675")
    g.add((url_height, RDF.type, crm.E55_Type))
    g.add((url_height, RDF.type, SKOS.Concept))
    g.add((url_height, SKOS.prefLabel, Literal("height")))
    g.add((url_height, SKOS.exactMatch, URIRef("http://collection.britishart.yale.edu/id/object/142/height")))
    concepts_urls["height"] = url_height
    
    # generating width triplets
    url_width = URIRef(str_url + "a7134177-6228-4716-8f90-b4e1d8514e63")
    g.add((url_width, RDF.type, crm.E55_Type))
    g.add((url_width, RDF.type, SKOS.Concept))
    g.add((url_width, SKOS.prefLabel, Literal("width")))
    g.add((url_width, SKOS.exactMatch, URIRef("http://collection.britishart.yale.edu/id/object/142/width")))
    concepts_urls["width"] = url_width
    
    # generating depth triplets
    url_width = URIRef(str_url + "60930303-fa6f-4fb8-9775-3d42b24603c8")
    g.add((url_width, RDF.type, crm.E55_Type))
    g.add((url_width, RDF.type, SKOS.Concept))
    g.add((url_width, SKOS.prefLabel, Literal("depth")))
    concepts_urls["depth"] = url_width
    
    # generating centimeters triplets
    url_cm = URIRef(str_url + "2f367772-afde-40ee-83bf-0690af8df959")
    g.add((url_cm, RDF.type, crm.E58_Measurement_Unit))
    g.add((url_cm, RDFS.label, Literal("centimeter")))
    concepts_urls["centimeter"] = url_cm
    
    # generating euterpe as an actor
    url_eut = URIRef(str_url + "f3aef059-6263-40ce-a23d-e14947f266b5")
    g.add((url_eut, RDF.type, crm.E39_Actor))
    g.add((url_eut, SKOS.prefLabel, Literal("Euterpe")))
    concepts_urls["euterpe"] = url_eut
    
    # generating référence bibliographique
    url_eut = URIRef(str_url + "ef00ea09-c863-4856-b97b-afc4cf78ba2b")
    g.add((url_eut, RDF.type, crm.E39_Actor))
    g.add((url_eut, SKOS.prefLabel, Literal("Référence bibliographique")))
    concepts_urls["url_bibli"] = url_eut
    
    # generating commentaire sur l'auteur
    url_com_period = URIRef(str_url + "50560569-d056-4242-bbfb-2ad78b8aa2be")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Attribution d'une période de production")))
    concepts_urls["url_com_aut"] = url_com_period
    
    # generating commentaire sur l'école
    url_com_ecole = URIRef(str_url + "02448e22-a17b-4428-af07-29efa8cd0b7d")
    g.add((url_com_ecole, RDF.type, crm.E55_Type))
    g.add((url_com_ecole, RDF.type, SKOS.Concept))
    g.add((url_com_ecole, SKOS.prefLabel, Literal("Attribution d'une école")))
    concepts_urls["url_ecole"] = url_com_ecole
    
    # generating commentaire sur la période
    url_com_ecole = URIRef(str_url + "1594d39b-ec41-46aa-ae95-21a6de8b43c3")
    g.add((url_com_ecole, RDF.type, crm.E55_Type))
    g.add((url_com_ecole, RDF.type, SKOS.Concept))
    g.add((url_com_ecole, SKOS.prefLabel, Literal("Attribution d'une période")))
    concepts_urls["url_period"] = url_com_ecole
    
    # generating identification d'un instrument
    url_com_ecole = URIRef(str_url + "52d168d7-588d-470b-8571-7d7105a419b0")
    g.add((url_com_ecole, RDF.type, crm.E55_Type))
    g.add((url_com_ecole, RDF.type, SKOS.Concept))
    g.add((url_com_ecole, SKOS.prefLabel, Literal("Identification d'un instrument")))
    concepts_urls["url_instru"] = url_com_ecole
    
    # generating identification d'une inscription
    url_com_ecole = URIRef(str_url + "0cae9d75-7d62-4a07-9649-8fb80fd58895")
    g.add((url_com_ecole, RDF.type, crm.E55_Type))
    g.add((url_com_ecole, RDF.type, SKOS.Concept))
    g.add((url_com_ecole, SKOS.prefLabel, Literal("Identification d'une inscription")))
    concepts_urls["url_inscri"] = url_com_ecole
    
    # generating indication sur la technique
    url_com_ecole = URIRef(str_url + "13fd08a2-6544-4837-b7e9-60689335557e")
    g.add((url_com_ecole, RDF.type, crm.E55_Type))
    g.add((url_com_ecole, RDF.type, SKOS.Concept))
    g.add((url_com_ecole, SKOS.prefLabel, Literal("Indication sur la technique")))
    concepts_urls["url_ind_tech"] = url_com_ecole
    
    # generating indication sur le theme
    url_com_ecole = URIRef(str_url + "91363850-ed4d-4648-8a6a-6970ccb42c3c")
    g.add((url_com_ecole, RDF.type, crm.E55_Type))
    g.add((url_com_ecole, RDF.type, SKOS.Concept))
    g.add((url_com_ecole, SKOS.prefLabel, Literal("Indication sur la thématique iconographique")))
    concepts_urls["url_theme"] = url_com_ecole
    
    # generating commentaire sur l'oeuvre
    url_com_period = URIRef(str_url + "43a24974-036b-4f3e-9427-a77e19382a61")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Commentaire sur l'oeuvre")))
    concepts_urls["url_com_oeuvre"] = url_com_period
    
    # generating commentaire sur l'instrument
    url_com_period = URIRef(str_url + "8133a385-23c0-4f12-be08-848acd254013")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Commentaire sur l'instrument")))
    concepts_urls["url_com_instru"] = url_com_period
    
    # generating identification type acteurs chantants
    url_com_period = URIRef(str_url + "15810704-95a0-4e46-9fa2-583febc6f589")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Type d'acteurs chantant")))
    concepts_urls["url_chant"] = url_com_period
    
    # generating commentaire oeuvre en rapport
    url_com_period = URIRef(str_url + "1eefcc32-fc65-4d6e-be1d-37d887f3be76")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Oeuvre en rapport")))
    concepts_urls["url_oeuvre_rapport"] = url_com_period
    
    # generating commentaire sur musique
    url_com_period = URIRef(str_url + "7db6da68-07b5-4552-b367-5807bdee2289")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Commentaire sur la musique")))
    concepts_urls["url_com_mus"] = url_com_period
    
    # generating commentaire source littéraire
    url_com_period = URIRef(str_url + "46aebde5-b8be-4913-a520-5bc347d6be42")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Source littéraire")))
    concepts_urls["url_source_litt"] = url_com_period
    
    # generating identification notation musicale
    url_com_period = URIRef(str_url + "8f8396c7-f6d7-4dd0-b2b2-6af39cd58741")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Identification d'une notation musicale")))
    concepts_urls["url_not_music"] = url_com_period
    
    # generating musical work visible in the painting
    url_com_period = URIRef(str_url + "d192e230-7561-4a97-8b33-d575ce31aee7")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Oeuvre musicale représentée")))
    concepts_urls["url_oeuvre_mus"] = url_com_period
    
    # generating attribution of painting school
    url_com_period = URIRef(str_url + "5a9cf85c-1a14-43af-8bdd-7009dfd38b57")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Attribution d'une école d'un peintre")))
    concepts_urls["url_paint_school"] = url_com_period
    
    # generating attribution 
    url_com_period = URIRef(str_url + "78bfcf8f-02d0-4aa3-9cc4-dd3997ca7ded")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Attribution à un autheur")))
    concepts_urls["url_attri"] = url_com_period
    
    # generating former attribution
    url_com_period = URIRef(str_url + "0ca8717b-3fe0-401e-b7de-57e8fb9ade8e")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Ancienne attribution")))
    concepts_urls["url_former_attribution"] = url_com_period
    
    # generating inspired from a painter
    url_com_period = URIRef(str_url + "ac7082de-739e-4141-b4c7-ae697b5f57d2")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Inspiré de l'oeuvre d'un autre auteur")))
    concepts_urls["url_dapres"] = url_com_period
    
    # generating attribution to an atelier of a painter
    url_com_period = URIRef(str_url + "4f927026-0e56-412c-a896-db4fef29fe85")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("De l'atelier d'un peintre")))
    concepts_urls["url_atelier"] = url_com_period
    
    # generating copy from a painter's work
    url_com_period = URIRef(str_url + "479c10c3-7e10-4a2b-b82b-b2440a508e6b")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Copie d'après")))
    concepts_urls["url_copy"] = url_com_period
    
    # generating à la manière de
    url_com_period = URIRef(str_url + "3bcedda1-f669-4bf2-8fd0-e1cc40d517c7")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("À la manière de")))
    concepts_urls["url_manière"] = url_com_period
    
    # generating genre de
    url_com_period = URIRef(str_url + "d8b0f141-1865-4740-be95-0b78e8e1a0c6")
    g.add((url_com_period, RDF.type, crm.E55_Type))
    g.add((url_com_period, RDF.type, SKOS.Concept))
    g.add((url_com_period, SKOS.prefLabel, Literal("Genre de")))
    concepts_urls["url_genre"] = url_com_period
    
    return concepts_urls, g


def GenerateTurtleAuthors(crm, eut_auteurs, concepts_urls, nb_r):
    """
    Parameters: crm namespace object, database for authors, dictionary of our concepts
    Fun: generates a rdf graph modelling the authors (cidoc crm ontology)

    """
    
    # creating the graph object
    g = Graph()
    
    # we load a number used for uuri generation
    rand_nb = random.Random()
    
    # string used to generate urls
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # generate prefixes
    g.bind("skos", SKOS)
    g.bind("crm", crm)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    
    # looping through the rows
    for i in range(len(eut_auteurs)):
        auteur = eut_auteurs.iloc[i]
        
        # generating the person
        g.add((URIRef(auteur["uri"]), RDF.type, crm.E21_Person))
        
        # adding the name
        g.add((URIRef(auteur["uri"]), crm.p1_is_identified_by, URIRef(auteur["nom_url"])))
        g.add((URIRef(auteur["nom_url"]), RDF.type, crm.E41_Appellation))
        g.add((URIRef(auteur["nom_url"]), RDFS.label, Literal(auteur["nom"])))
        
        # adding birth, generating an url for the timespan
        if auteur["date_de_naissance"] is np.nan:
            None
        else:
            rand_nb.seed(nb_r)
            url_timespan1 = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((URIRef(auteur["uri"]), crm.p98i_was_born, URIRef(auteur["date_de_naissance_url"])))
            g.add((URIRef(auteur["date_de_naissance_url"]), RDF.type, crm.E67_Birth))
            g.add((URIRef(auteur["date_de_naissance_url"]), crm.p4_has_timespan, url_timespan1))
            g.add((url_timespan1, RDF.type, crm.E52_Timespan))
            g.add((url_timespan1, RDFS.label, Literal(auteur["date_de_naissance"])))
        
        # adding death, generating an url for the timespan
        if auteur["date_de_deces"] is np.nan:
            None
        else:
            rand_nb.seed(nb_r)
            url_timespan2 = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((URIRef(auteur["uri"]), crm.p100i_died_in, URIRef(auteur["date_de_deces_url"])))
            g.add((URIRef(auteur["date_de_deces_url"]), RDF.type, crm.E69_Death))
            g.add((URIRef(auteur["date_de_deces_url"]), crm.p4_has_timespan, url_timespan2))
            g.add((url_timespan2, RDF.type, crm.E52_Timespan))
            g.add((url_timespan2, RDFS.label, Literal(auteur["date_de_deces"])))
            
        # adding speciality as a type
        if auteur["specialite_tid"] is np.nan:
            None
        elif len(auteur["specialite_tid"].split(sep=" , ")) > 1 :
            for spe in auteur["specialite_tid"].split(sep=" , "):
                g.add((URIRef(auteur["uri"]), crm.p2_has_type, URIRef(spe)))
        else:
            g.add((URIRef(auteur["uri"]), crm.p2_has_type, URIRef(URIRef(auteur["specialite_tid"]))))
            
        
        ## adding commentaire as an attribute
        if auteur["commentaire"] is np.nan:
            None
        else:
            rand_nb.seed(nb_r)
            url_attri = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_attri, RDF.type, crm.E13_Attribute))
            g.add((url_attri, crm.p140_assigned_attribute_to, URIRef(auteur["uri"])))
            g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
            g.add((url_attri, crm.p177_assigned_property_type, concepts_urls["url_com_aut"] ))
            g.add((url_attri, crm.p141_assigned, URIRef(auteur["commentaire_url"])))
            g.add((URIRef(auteur["commentaire_url"]), RDF.type, crm.E73_Information_Object))
            g.add((URIRef(auteur["commentaire_url"]), RDFS.label, Literal(auteur["commentaire"])))
        
    # outputting the rdfs as a turtle file
    g.serialize(destination='output/auteurs.ttl', format='turtle')
    
    return nb_r


def AddingTidAttribute(g, piece, rand_nb, nb_r, piece_url, concepts_urls, tid,
                       url_concept):
    """
    parameters (in order): rdf graph, data of the art piece, random number 
            generator object, index for number generation, url of the art 
            piece, dictionary of our concepts, field for the thesauri as a string,
            key for the url of the attribute type
    fun: adds a thesauri to an art work as an E13 attribute. Used for assertion
         relative to scientifical debates
    """
    
    # string for generating urls
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # in case of nan value
    if piece[tid] is np.nan:
        None
        
    # if multiple values
    elif len(piece[tid].split(sep=" , ")) > 1 :
        for instru in piece[tid].split(sep=" , "):
            rand_nb.seed(nb_r)
            url_attri = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_attri, RDF.type, crm.E13_Attribute))
            g.add((url_attri, crm.p140_assigned_attribute_to, piece_url))
            g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
            g.add((url_attri, crm.p177_assigned_property_type, concepts_urls[url_concept] ))
            g.add((url_attri, crm.p141_assigned, URIRef(instru)))
            
    # if unique value
    else:
        rand_nb.seed(nb_r)
        url_attri = generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        g.add((url_attri, RDF.type, crm.E13_Attribute))
        g.add((url_attri, crm.p140_assigned_attribute_to, piece_url))
        g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
        g.add((url_attri, crm.p177_assigned_property_type, concepts_urls[url_concept] ))
        g.add((url_attri, crm.p141_assigned, URIRef(piece[tid])))
        
    return g, nb_r


def AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url, concepts_urls, col_com,
                       url_concept, crm_instance):
    """
    similar to AddingTidAttribute, but adds a commentary as a string instead
    of a thesauri
    """
    
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    if piece[col_com] is np.nan:
        None
    else:
        rand_nb.seed(nb_r)
        url_attri = generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        g.add((url_attri, RDF.type, crm.E13_Attribute))
        g.add((url_attri, crm.p140_assigned_attribute_to, piece_url))
        g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
        g.add((url_attri, crm.p177_assigned_property_type, concepts_urls[url_concept] ))
        g.add((url_attri, crm.p141_assigned, URIRef(piece[col_com+"_url"])))
        g.add((URIRef(piece[col_com+"_url"]), RDF.type, crm_instance))
        g.add((URIRef(piece[col_com+"_url"]), RDFS.label, Literal(piece[col_com])))
    
    return g, nb_r


def GenerateTurtleMusicWorks(crm, eut_music_works, concepts_urls, eut_auteurs, nb_r):
    """
    parameters: crm namespace object, database of the lyrical works as a df,
            dictionary of our concepts, database of our authors as a df
    fun: generates a rdf graph for the lyrical works

    """
    # creating the graph object
    g = Graph()
    
    # we load a number used for uuri generation
    rand_nb = random.Random()
    
    # string used to generate urls
    str_url = "http://data-iremus.huma-num.fr/id/"
    
    # generate prefixes
    g.bind("skos", SKOS)
    g.bind("crm", crm)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    
    # looping through the rows
    for i in range(len(eut_music_works)):
        work = eut_music_works.iloc[i]
        
        # loading the uri of the work
        uri_work = URIRef(work["uri"])
        
        # generating the instance E73s
        g.add((uri_work, RDF.type, crm.E73_Information_Object))
        
        # generating the type of musical work
        if work["type_oeuvre_tid"] is np.nan:
            None
        else:
            g.add((uri_work, crm.p2_has_type, URIRef(work["type_oeuvre_tid"])))
        
        # adding the title object E35
        g.add((uri_work, crm.p102_has_title, URIRef(work["titre_de_l_oeuvre_url"])))
        g.add((URIRef(work["titre_de_l_oeuvre_url"]), RDF.type, crm.E35_Title))
        g.add((URIRef(work["titre_de_l_oeuvre_url"]), RDFS.label,
               Literal(work["titre_de_l_oeuvre"])))
        
        ## adding commentaire as an attribute
        if work["commentaire"] is np.nan:
            None
        else:
            rand_nb.seed(nb_r)
            url_attri = generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((url_attri, RDF.type, crm.E13_Attribute))
            g.add((url_attri, crm.p140_assigned_attribute_to, uri_work))
            g.add((url_attri, crm.p14_carried_out_by, concepts_urls["euterpe"] ))
            g.add((url_attri, crm.p177_assigned_property_type, concepts_urls["url_com_oeuvre"] ))
            g.add((url_attri, crm.p141_assigned, URIRef(work["commentaire_url"])))
            g.add((URIRef(work["commentaire_url"]), RDF.type, crm.E73_Information_Object))
            g.add((URIRef(work["commentaire_url"]), RDFS.label, Literal(work["commentaire"])))
            
        ## working on the production object
        # generating production instance
        rand_nb.seed(nb_r)
        url_prod = generate_rdf_url(rand_nb, str_url)
        g.add((url_prod, RDF.type, crm.E65_Creation))
        g.add((url_prod, crm.p94_has_created, uri_work))
        nb_r += 1
        
        # artist
        g, nb_r = AddingCreators(work["librettiste_target_id"], g, nb_r,
                                      rand_nb, url_prod, concepts_urls, eut_auteurs)
        
        g, nb_r = AddingCreators(work["compositeur_target_id"], g, nb_r,
                                      rand_nb, url_prod, concepts_urls, eut_auteurs)
        
    # outputting the rdfs as a turtle file
    g.serialize(destination='output/oeuvres_lyriques.ttl', format='turtle')
    
    return nb_r