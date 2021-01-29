import os
import json
import logging
from .callwatcher.client import insert_callout_result
from .xmlrpc.client import rpcserver
from types import SimpleNamespace

DEBUG=False
### Api Wrapper    
server = rpcserver("localhost",8000)
def query_choice(sentences, answer):
    return server.distance(sentences, answer)
    
### Read Survey
questions = []
it = None
question_count = 0
class Question(object):
    def __init__(self, question, type, options):
        self.question = question
        self.type = type
        self.options = options
        self.answer = None
        self.choice = None
        self.result = None
    
    def respond_answer(self, answer):
        self.answer = answer
        if self.type == "03":
            self.result = answer
            return 
        choice, index = query_choice(self.options, answer)
        self.choice = choice
        self.result = index
        
    def render_type(self):
        if self.type == "01":
            return "[单选题]"
        if self.type == "02": 
            return "[多选题]"
        return "[问答题]"
            
    def render_options(self):
        return "，".join(self.options)
        
    def render(self):
        return f"{self.render_type()} {self.question} {self.render_options()}"

### Call back Functions
def init_survey(user_utter, global_vars, context = None):
    f = open("data/data.json", "r")
    survey = json.load(f)
    for data in survey:
        question = data['quest_name']
        quest_type = data['quest_type']
        array = data.get('daarray',[])
        if array: 
            options = [o['daname'] for o in array]
        else:
            options = []    
        questions.append(Question(question, quest_type, options))
    question_count = len(questions)
    global it
    it = iter(questions)
    return True

def next_question(user_utter, global_vars, context = None):
    quest = next(it, None)
    # set question
    global_vars['question'] = quest
    if quest:
        return quest.render()
    else:
        return False
        
def answer_to_choice(user_utter, global_vars, context = None):
    answer = global_vars['answer']
    quest = global_vars['question']
    quest.respond_answer(answer)
    logging.info(f"answer_to_choice {answer} in {quest.options}, got {quest.choice}, {quest.result}")
    global_vars['result'] = str(global_vars['result']) + f"#{quest.result}"
    # clear question-answer pair
    global_vars['answer'] = None
    global_vars['question'] = None
    return True

def save(user_utter, global_vars, context = None):
    ns = SimpleNamespace(**context)
    call_id = ns.call_info['call_id']
    extend = ns.call_info['extend']
    stringToInt = extend.split("#")[0]
    try:
      from_callid = int(stringToInt)
    except ValueError:
      from_callid = -1
    content = "#".join(ns.history)
    # global variables
    call_result = global_vars['result']
    logging.info(f"write_result: extend={extend},call_result={call_result}")
    insert_callout_result(call_id, from_callid, content, extend, call_result)
    return True
    
if __name__ == "__main__":
    pass
     
    