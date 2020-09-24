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
from rdflib import Graph
from rdflib.namespace import Namespace
from rdflib import Graph, RDF, URIRef, Literal, RDFS, XSD
from rdflib.namespace import SKOS
import random
import numpy as np
import json

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/GIT")

# importing our functions
import python.functions as fun

# generating cidoc crm namespace
crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
iremus = Namespace('http://data-iremus.huma-num.fr/id/')

# copying our original excel sheet in the output
shutil.copyfile('input/taxonomies.xlsx', 'output/taxonomies_modified.xlsx')

### extracting and saving iconclass codes
print(
"""
We download the json containing all skos codes of iconclass from
iconclass.org, and we save the codes in a csv
"""
)

if os.path.isfile('output/icon_class_codes.csv'):
    # extracting our themes in a list
    iconclasses_list = list(pd.read_csv("output/icon_class_codes.csv")["codes"])
else:
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
our turtle rdfs. We then build our urls and store them in the dataframe.
"""
)

## this number will be used throughout the file to generate new uuris
nb_r = 10 **5

## looping throught the different excel sheets and generating a turtle file for each
taxo, nb_r = fun.GenerateTtlThesauri(thes_list, taxo, nb_r)

# changing special thesauri
fun.GenerateTtlSpecialThesauri(taxo, "Période", crm.E4_Period,
                               "94b50b0d-7202-4c5f-86a7-098cde58f2ee")
fun.GenerateTtlSpecialThesauri(taxo, "Thème", crm.E28_Conceptual_Object,
                               "ed05ac60-c461-4eab-be00-d9dd8f816cda")
    
### calculating coordinates
print(
"""
We extract the citys name from 'lieu de conservation' and load its corresponding
coordinates in WGS84 (coordinate system), then saving it into the dataframe
With a slow connection this might takes some time
"""
)

# if the coordinates are not extracted we save them 
if os.path.isfile('output/coordinates.json'):
    None
else:
    ## extracting cities strings and putting them in a list
    # extracting our themes in a list
    names = list(taxo["Lieu de conservation"]["name"])
    
    # extracting the coordinates from the list of names and the dataframe
    dict_coords = fun.ExtractCoordinates(names, "collection privée")
    
    # we save into a json
    with open('output/coordinates.json', 'w', encoding='utf8') as fp:
        json.dump(dict_coords, fp, ensure_ascii=False)
        
        
# importing the coordinates
with open('output/coordinates.json', encoding='utf8') as json_file:
    dict_coords = json.load(json_file)
        
# generating the rdf for places
nb_r = fun.GenerateTtlPlaces(taxo, nb_r, dict_coords)

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

### generate the ttl for all paintings
print(
"""
We start to generate the ttl for all the paintings of our database
"""
)

# loading euterp data
eut_data = pd.read_excel("output/euterpe_data_modified.xlsx", sheet_name="4_euterpe_images")

# loading persons
eut_auteurs = pd.read_excel("output/euterpe_data_modified.xlsx", sheet_name="1_auteurs")

# creating the graph object for our concepts
g = Graph()

# generate prefixes
g.bind("skos", SKOS)
g.bind("crm", crm)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("iremus", iremus)

## generating general concepts
# creating a dictionary to store our general concepts
concepts_urls, g = fun.GeneratingGeneralConcepts(g, crm)

# outputting the rdfs as a turtle file
g.serialize(destination='output/concepts.ttl', format='turtle')

# creating the graph object
g = Graph()

# generate prefixes
g.bind("skos", SKOS)
g.bind("crm", crm)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("iremus", iremus)

# we load a number used for uuri generation
rand_nb = random.Random()

# string used to generate urls
str_url = "http://data-iremus.huma-num.fr/id/"

# looping through the rows
for i in range(len(eut_data)):
    
    # loading one painting
    piece = eut_data.iloc[i]
    
    # generating our random number for url generation
    rd = random.Random()
    rd.seed(nb_r)
    
    # loading the url of the painting
    piece_url = URIRef(piece["uri"])
    
    # creating cidoc instance E22
    g.add((piece_url, RDF.type, crm.E22_ManMade_Object))
    
    
    # adding the title object E35
    g.add((piece_url, crm.p102_has_title, URIRef(piece["titre_url"])))
    g.add((URIRef(piece["titre_url"]), RDF.type, crm.E35_Title))
    g.add((URIRef(piece["titre_url"]), RDFS.label, Literal(piece["titre"])))
    
    # adding paintings in relation
    if piece["voir_aussi_target_id"] is np.nan:
        None
    elif len(piece["voir_aussi_target_id"].split(sep=" , ")) > 1 :
        for peint in piece["voir_aussi_target_id"].split(sep=" , "):
            g.add((piece_url, RDFS.seeAlso,
               URIRef(peint)))
    else:
        g.add((piece_url, RDFS.seeAlso,
               URIRef(piece["voir_aussi_target_id"])))
    
    # generating p53 location, linking with the ttl location
    if piece["lieu_de_conservation_tid"] is np.nan:
        None
    elif len(piece["lieu_de_conservation_tid"].split(sep=" , ")) > 1 :
        for lieu in piece["lieu_de_conservation_tid"].split(sep=" , "):
            g.add((piece_url, crm.p53_has_former_or_current_location,
               URIRef(lieu)))
    else:
        g.add((piece_url, crm.p53_has_former_or_current_location,
               URIRef(piece["lieu_de_conservation_tid"])))
    
    ## generating dimension properties and instances
    if piece["hauteur"] is np.nan:
        None
    else:
        # linking with the E22
        g.add((piece_url, crm.p43_has_dimension,
               URIRef(piece["hauteur_url"])))
        
        # loading E54 dimension instance
        g.add((URIRef(piece["hauteur_url"]), RDF.type, crm.E54_Dimension))
        
        # linking with types
        g.add((URIRef(piece["hauteur_url"]), crm.p2_has_type, concepts_urls["height"]))
        g.add((URIRef(piece["hauteur_url"]), crm.p91_has_unit, concepts_urls["centimeter"]))
        
        # adding the value
        g.add((URIRef(piece["hauteur_url"]), crm.p90_has_value,
               Literal(piece["hauteur"], datatype=XSD.float)))
        
    # adding for diameter
    if piece["diametre"] is np.nan:
        None
    else:
        # linking with the E22
        g.add((piece_url, crm.p43_has_dimension,
               URIRef(piece["diametre_url"])))
        
        # loading E54 dimension instance
        g.add((URIRef(piece["diametre_url"]), RDF.type, crm.E54_Dimension))
        
        # linking with types
        g.add((URIRef(piece["diametre_url"]), crm.p2_has_type, concepts_urls["diameter"]))
        g.add((URIRef(piece["diametre_url"]), crm.p91_has_unit, concepts_urls["centimeter"]))
        
        # adding the value
        g.add((URIRef(piece["diametre_url"]), crm.p90_has_value,
               Literal(piece["diametre"], datatype=XSD.float)))
        
    # adding for width
    if piece["largeur"] is np.nan:
        None
    else:
        g.add((piece_url, crm.p43_has_dimension,
               URIRef(piece["largeur_url"])))
        g.add((URIRef(piece["largeur_url"]), RDF.type, crm.E54_Dimension))
        g.add((URIRef(piece["largeur_url"]), crm.p2_has_type, concepts_urls["width"]))
        g.add((URIRef(piece["largeur_url"]), crm.p91_has_unit, concepts_urls["centimeter"]))
        g.add((URIRef(piece["largeur_url"]), crm.p90_has_value,
               Literal(piece["largeur"], datatype=XSD.float)))
        
    # adding for depth
    if piece["profondeur_en_cm"] is np.nan:
        None
    else:
        g.add((piece_url, crm.p43_has_dimension,
               URIRef(piece["profondeur_en_cm_url"])))
        g.add((URIRef(piece["profondeur_en_cm_url"]), RDF.type, crm.E54_Dimension))
        g.add((URIRef(piece["profondeur_en_cm_url"]), crm.p2_has_type, concepts_urls["depth"]))
        g.add((URIRef(piece["profondeur_en_cm_url"]), crm.p91_has_unit, concepts_urls["centimeter"]))
        g.add((URIRef(piece["profondeur_en_cm_url"]), crm.p90_has_value,
               Literal(piece["profondeur_en_cm"], datatype=XSD.float)))
        
    # creating the image object
    if piece["image_fid"] is np.nan:
        None
        
    # for multiple images
    elif len(piece["image_fid"].split(sep=" 🍄 ")) > 1 :
        for img_id in piece["image_fid"].split(sep=" 🍄 "):
            rand_nb.seed(nb_r)
            url_img = fun.generate_rdf_url(rand_nb, str_url)
            nb_r += 1
            g.add((piece_url, crm.p138i_has_representation, url_img))
            g.add((url_img, RDF.type, crm.E36_visual_item))
            g.add((url_img, RDFS.label, Literal(img_id)))
            
    # for single image
    else:
        rand_nb.seed(nb_r)
        url_img = fun.generate_rdf_url(rand_nb, str_url)
        nb_r += 1
        g.add((piece_url, crm.p138i_has_representation, url_img))
        g.add((url_img, RDF.type, crm.E36_visual_item))
        g.add((url_img, RDFS.label, Literal(piece["image_fid"])))
    
    ## working on the production object
    # generating production instance
    rand_nb.seed(nb_r)
    url_prod = fun.generate_rdf_url(rand_nb, str_url)
    g.add((url_prod, RDF.type, crm.E12_Production))
    g.add((url_prod, crm.p108_has_produced, piece_url))
    nb_r += 1
    
    # adding the domain (type of work, e.g. painting)
    if piece["domaine_tid"] is np.nan:
        None
    elif len(piece["domaine_tid"].split(sep=" , ")) > 1 :
        for domaine in piece["domaine_tid"].split(sep=" , "):
            g.add((url_prod, crm.p32_used_general_technique, URIRef(domaine)))
    else:
        g.add((url_prod, crm.p2_has_type, URIRef(piece["domaine_tid"])))
    
    # generating date production
    if piece["date_oeuvre"] is np.nan:
        None
    else:
        g.add((url_prod, crm.p4_has_timespan, URIRef(piece["date_oeuvre_url"])))
        g.add((URIRef(piece["date_oeuvre_url"]), RDF.type, crm.E52_Timespan))
        g.add((URIRef(piece["date_oeuvre_url"]), RDFS.label, Literal(piece["date_oeuvre"])))
    
    ## generating producers
    # attributed author
    g, nb_r = fun.AddingAttributedProducer(piece["attribu__target_id"], g,
                                           nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_attri")
    
    # attributed school
    g, nb_r = fun.AddingAttributedProducer(piece["_cole_de_target_id"],
                                           g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_paint_school")
    
    # former attribution
    g, nb_r = fun.AddingAttributedProducer(piece["ancienne_attribution_target_id"],
                                           g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_former_attribution")
    
    # copy from a certain painter's work
    g, nb_r = fun.AddingAttributedProducer(piece["d_apr_s_target_id"],
                                           g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_dapres")
    
    # painting from an atelier of a painter
    g, nb_r = fun.AddingAttributedProducer(piece["atelier_de_target_id"],
                                           g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_atelier")
    
    # painting copied from an author's work
    g, nb_r = fun.AddingAttributedProducer(piece["copie_d_apr_s_target_id"],
                                           g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_copy")
    
    # painting à la manière de
    g, nb_r = fun.AddingAttributedProducer(piece["mani_re_de_target_id"],
                                           g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_manière")
    
    # inventeur
    g, nb_r = fun.AddingAttributedProducer(piece["inventeur_target_id"], g, nb_r,
                                  rand_nb, concepts_urls, eut_auteurs, piece_url,
                                  "url_invent")
    
    # painting genre de
    g, nb_r = fun.AddingAttributedProducer(piece["genre_de_target_id"],
                                           g, nb_r, rand_nb, url_prod,
                             concepts_urls, eut_auteurs, piece_url, "url_genre")
    
    # artist
    g, nb_r = fun.AddingProducers(piece["artiste_target_id"], g, nb_r,
                                  rand_nb, url_prod, concepts_urls, eut_auteurs,
                                  "524db20d-156d-4c1e-b60f-a69e59b722ea")
    
    # éditeur
    g, nb_r = fun.AddingProducers(piece["_diteur_target_id"], g, nb_r,
                                  rand_nb, url_prod, concepts_urls, eut_auteurs,
                                  "8a2902e4-434f-461d-882e-9c243ebef0b2")
    
    # graveur
    g, nb_r = fun.AddingProducers(piece["graveur_target_id"], g, nb_r,
                                  rand_nb, url_prod, concepts_urls, eut_auteurs,
                                  "2b20adc9-54a8-4573-8347-2a994809e622")
    
    ## adding the tids (thesauris)
    # adding the musical instrument as an attribution
    g, nb_r = fun.AddingTidAttribute(g, piece, rand_nb, nb_r, piece_url, concepts_urls,
                                     "instrument_de_musique_tid", "url_instru")
    
    # adding represented oeuvre musicale as an attribution
    g, nb_r = fun.AddingTidAttribute(g, piece, rand_nb, nb_r, piece_url, concepts_urls,
                                     "_oeuvre_repr_sent_e_target_id", "url_oeuvre_mus")

    # adding the represented musical works as an attribute
    g, nb_r = fun.AddingTidAttribute(g, piece, rand_nb, nb_r, piece_url, concepts_urls,
                                     "_oeuvre_repr_sent_e_target_id", "url_oeuvre_mus")
    
    # adding the musical notation in the piece
    g, nb_r = fun.AddingTidAttribute(g, piece, rand_nb, nb_r, piece_url, concepts_urls,
                                     "musique_ecrite_tid", "url_not_music")
    
    # adding the chant tid as an attribute
    g, nb_r = fun.AddingTidAttribute(g, piece, rand_nb, nb_r, piece_url, concepts_urls,
                                     "chant_tid", "url_chant")
    
    # adding the theme as an attribute
    g, nb_r = fun.AddingTidAttribute(g, piece, rand_nb, nb_r, piece_url, concepts_urls,
                                     "theme_tid", "url_theme")
    
    ## adding the various comments
    # adding inscription as an attribute
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "inscription",
                                         "url_inscri", crm.E34_Inscription)
    
    # adding the bibliography
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "bibliographie",
                                         "url_bibli", crm.E73_Information_Object)
    
    # adding comment on the technique
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, url_prod,
                                         concepts_urls, "technique", "url_ind_tech",
                                         crm.E73_Information_Object)
    
    # adding comment on similar paintings
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "oeuvre_en_rapport", "url_oeuvre_rapport",
                                         crm.E73_Information_Object)
    
    # adding commentaire sur l'oeuvre precision_oeuvre
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "precision_oeuvre",
                                         "url_com_oeuvre", crm.E73_Information_Object )
    
    # adding commentaire sur l'instrument pr_cision_instrument
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "pr_cision_instrument",
                                         "url_com_instru", crm.E73_Information_Object)
    
    # adding commentaire sur l'oeuvre (other column)
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "commentaire",
                                         "url_com_oeuvre", crm.E73_Information_Object)
    
    # adding comment on the music
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "pr_cision_musique",
                                         "url_com_mus", crm.E73_Information_Object)
    
    # adding reference to a literary work
    g, nb_r = fun.AddingCommentAttribute(piece, rand_nb, nb_r, g, piece_url,
                                         concepts_urls, "source_litteraire",
                                         "url_source_litt", crm.E73_Information_Object)
    
# outputting the rdfs as a turtle file
g.serialize(destination='output/euterpe_data.ttl', format='turtle')

### generating a turtle with cidoc modellisation for the authors
print("""
      We generate a ttl rdf for the autheurs, with a cidoc modellisation
      """)
      
nb_r = fun.GenerateTurtleAuthors(crm, eut_auteurs, concepts_urls, nb_r)

### generating a turtle with cidoc modellisation for the musical works
print("""
      We generate a ttl rdf for lyrical works
      """)
      
# loading musical works
eut_music_works = pd.read_excel("output/euterpe_data_modified.xlsx", sheet_name="5_oeuvres_lyriques")

nb_r = fun.GenerateTurtleMusicWorks(crm, eut_music_works, concepts_urls, eut_auteurs)

