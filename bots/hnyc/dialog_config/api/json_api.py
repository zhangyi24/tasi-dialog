import requests
import configparser
import urllib
import os
import json

DEBUG=False

def request(endpoint, params = None):
    headers = {}
    domain = "http://localhost:3000"
    path = "/"
    url = f"{domain}{path}{endpoint}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
    response = requests.get(url,headers=headers)
    if DEBUG:
        print(f"{response.request.method} -- {response.url}\n",f"{response.text}")
        
    if not response.json():
        return None
    return response.json()[0]

def query(endpoint='users', cert_no=None, phone_no=None):
    endpoint = 'users'
    if cert_no:
        return request(endpoint,{'cert_no':cert_no})
    if phone_no:
        return request(endpoint,{'phone':phone_no})