import requests
import configparser
import urllib
from jsonpath_ng import jsonpath, parse
from datetime import datetime, timedelta
import os
import json
import logging
#
# API_CONFIG = object()
# setattr(API_CONFIG,"domain","localhost:3000")
DEBUG=False
### Api Wrapper    
def request(endpoint, params = None):
    headers = {}
    domain = "http://localhost:3000"
    url = f"{domain}{endpoint}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
    response = requests.get(url,headers=headers)
    if DEBUG:
        print(f"{response.request.method} -- {response.url}\n",f"{response.text}")
        
    if not response.json():
        return None
    return response.json()[0]

def get_user(cert_no, phone):
    if cert_no:
        return request(f'/users',{'cert_no':cert_no})
    if phone:
        return request(f'/users',{'phone':phone})
        

### Call back Functions
def consumer_info_access_by_phone_no(user_utter, global_vars):
    logging.debug(f"consumer_info_access_by_phone_no: user_utter={user_utter}, global_vars={global_vars}")
    data = get_user(None, global_vars['phone_no'])
    if not data:
        return False
    else:
        global_vars['consumer_info'] = data
        return True
    
def consumer_info_access_by_cert_no(user_utter, global_vars):   
    logging.debug(f"consumer_info_access_by_cert_no: user_utter={user_utter}, global_vars={global_vars}")
    data = get_user(global_vars['cert_no'], None)
    if not data:
        return False
    else:
        global_vars['consumer_info'] = data
        return True
        
def report_consumer_info(user_utter, global_vars): 
    sales = global_vars['consumer_info']['sales']
    sales_phone = global_vars['consumer_info']['sales_phone']
    return f"您的售货员是{sales},售货员电话{sales_phone}"
    
if __name__ == "__main__":
    phone_no = 13588880000
    cert_no = 22345678
    res = request(f'/users',{'cert_no':cert_no})
    print(res)
     
    