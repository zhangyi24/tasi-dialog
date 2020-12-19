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

### Read Survey
questions = []
question_count = 0
survey_type = 'survey'        

### Call back Functions
def survey_type(user_utter, global_vars, context = None):
    return survey_type
    
def init_survey(user_utter, global_vars, context = None):
    f = open("data/question-raw.json", "r")
    survey = json.load(f)
    for data in survey:
        question = data['quest_name']
        array = data.get('daarray',[])
        if array: 
            options = [o['daname'] for o in array]
        else:
            options = []
        answer = ",".join(options)
        questions.append(f"{question} {answer}")
    question_count = len(questions)
    survey_type = 'survey'

def next_question(user_utter, global_vars, context = None):
    if questions:
        return questions.pop(0)
    else:
        return False
    
if __name__ == "__main__":
    phone_no = 13588880000
    cert_no = 22345678
    res = request(f'/users',{'cert_no':cert_no})
    print(res)
     
    