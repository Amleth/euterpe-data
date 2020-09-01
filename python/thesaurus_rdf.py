# iremus 2020
# Project auterp rdf
# generate turtle rdfs from iremus thesaurus
# Cedric
# 01/09/2020

# setting work environment
import os
import pandas as pd
from rdflib import Graph, RDF, URIRef, Literal
from rdflib.namespace import SKOS, DC
import uuid
import random
from openpyxl import load_workbook
import shutil

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/project/taxonomie_turtle")

# copying our original excel sheet in the output
shutil.copyfile('input/taxonomies.xlsx', 'output/taxonomies.xlsx')

# creating a list with all our thesaurus
thes_list = ["spécialité", "Période", "École", "Mots matières", "Domaine",
             "Lieu de conservation", "Notation musicale", "Chant", "Support",
              "Type oeuvre"]

## looping throught the different excel sheets and generating a ttl for each
# creating our index to generate our random uuris
i = 0

for thes in thes_list:
    
    # extracting our themes in a list
    sheet = pd.read_excel("input/taxonomies.xlsx", sheet_name=thes)
    
    
    # creating the UURI for the conceptscheme
    scheme_uuri = URIRef("http://data-iremus.huma-num.fr/id/123test")
    
    ## making triples from the sheet
    # incrementing our index
    i += 1
    
    rd = random.Random()
    
    # creating the graph object
    g = Graph()
    
    ## creating the triple for the concept scheme
    # adding triples
    g.add((scheme_uuri, RDF.type, SKOS.ConceptScheme))
    g.add((scheme_uuri, DC.title, Literal(thes, lang="fr")))
    
    # list of uris
    uris = []
    
    for label in sheet.iloc[:,1]:
        
        # generating the uri
        rd.seed(i)
        uid = uuid.UUID(int=rd.getrandbits(128))
        uri = URIRef("http://data-iremus.huma-num.fr/id/" + str(uid))
        
        # storing the uri in a list to add it to the conceptscheme
        uris.append(uri)
        
        # adding the triples
        g.add((uri, RDF.type, SKOS.Concept))
        g.add((uri, SKOS.prefLabel, Literal(label, lang="fr")))
        g.add((uri, SKOS.inScheme, scheme_uuri))
        
        # incrementing the index for uuri generation
        i += 1
    
    # adding the uuri to the conceptscheme
    for ur in uris:
        g.add((scheme_uuri, SKOS.hasTopConcept, ur))
    
    # vizualizing the result
    #print(g.serialize(format="turtle").decode("utf-8"))
    
    # outputting the rdfs as a turtle file
    g.serialize(destination='output/'+thes+'.ttl', format='turtle')
    
    ## adding the uuris to our excel file
    # adding the uuris to the pd dataframe
    sheet["uuris"] = uris
    
    # loading the excel
    book = load_workbook("output/taxonomies.xlsx")
    
    # creating an excel sheet
    writer = pd.ExcelWriter("output/taxonomies.xlsx", engine = 'openpyxl')
    writer.book = book
    
    # remove the previous excel sheet and saving the file
    sheet_rem = book.get_sheet_by_name(thes)
    book.remove_sheet(sheet_rem)
    book.save('output/taxonomies.xlsx')
    
    # putting our new sheet into the excel
    sheet.to_excel(writer, index=False, sheet_name=thes, startrow=0)
    
    # saving the file
    writer.save()

