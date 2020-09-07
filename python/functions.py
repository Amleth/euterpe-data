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
    
    
