import re
import pandas as pd
import os, math
import csv
from src.utils.fileutils import filepath, joinpath

from cocoNLP.extractor import extractor
ex = extractor()

df = pd.read_excel(filepath(__file__, "../addr-5000.xls"))

def regex(string):
    string = string.replace(" ","")
    pat = re.compile('(\D{0,4}?(省|市|县|区|道|路|街|小区|里|居|园|亭|家|院|苑|城|大厦|公寓|商厦|支行|楼|号|门|门口|附近|对面|旁))*')
    res = pat.search(string)
    if res:
        return res.group()
    return ""
    
def nlp_addr(string):
    locations = ex.extract_locations(string)
    return next(iter(locations),"")
    
def regex_reason(string):
    pat = re.compile('((挡|堵|占|施工|碍事|画线|压|禁停|消防|没)\D*(门口|位置|车|车位|道|路|门|井盖|线|车窗)?)')
    res = pat.search(string)
    if res:
        return res.group()
    return ""
    
def reason(string):
    res = string.split(" ")[-1]
    return res

df['regex_addr'] = df[df.columns[0]].apply(regex)
df['nlp_addr'] = df[df.columns[0]].apply(nlp_addr)
df['reason'] = df[df.columns[0]].apply(reason)    
df['regex_reason'] = df[df.columns[0]].apply(regex_reason)
output = filepath(__file__, "../output.xls", ensure=True)
df.to_excel(output)
os.system(f"open {output}")


