import requests
import configparser
import urllib
from jsonpath_ng import jsonpath, parse
from datetime import datetime, timedelta
import os
import json

API_CONFIG = object()
API_CONFIG.domain = "localhost:3000"
DEBUG=False
### Api Wrapper    
def request(endpoint, params = None):
    headers = {}
    url = f"{API_CONFIG.domain}{endpoint}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
    response = requests.get(url,headers=headers)
    if DEBUG:
        print(f"{response.request.method} -- {response.url}\n",f"{response.text}")
    return response

def get_user(cert_no, phone):
    if cert_no:
        request(f'/users',{'cert_no':cert_no})
    if phone:
        request(f'/users',{'phone':phone})
        
        
     
    