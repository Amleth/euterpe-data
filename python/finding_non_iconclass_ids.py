# iremus 2020
# Project auterp rdf
# extract icon class codes
# Cedric
# 31/08/2020

# setting work environment
import os
import pandas as pd

# changing working directory
os.chdir("C:/Users/Cedric/Desktop/project")

# loading the csv into a list
iconclasses_df = pd.read_csv("icon_class_codes.csv")
iconclasses_list = list(iconclasses_df.iloc[:,1])

# extracting our themes in a list
themes = pd.read_excel("taxonomies.xlsx", sheet_name="Thème")
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
        
# creating a pd dataframe before exporting
dict_codes = {"modification" : modified}
df = pd.DataFrame(dict_codes)

# exporting the result as an excel
# we will then edit the excel manually
df.to_excel("modification_result.xlsx")

