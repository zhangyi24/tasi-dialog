from faker import Faker
fake = Faker('zh_CN')

import jsonpickle, os
from jsonpickle.pickler import Pickler
jsonpickle.set_preferred_backend('json')
jsonpickle.set_encoder_options('json', ensure_ascii=False, sort_keys=False, indent=2)

import json

def encode(obj):
    return jsonpickle.encode(obj, unpicklable=True)

def decode(obj):
    return jsonpickle.decode(obj)

class Model:
    def dump(self, filepath=None):
        if not filepath:
            filename = self.__class__.__name__.lower() + ".json"
            filepath = os.path.join("./data/", filename)

        data = encode(self)
        f = open(filepath,'w').write(data)
    
    def load(self, filepath=None):
        if not filepath:
            filename = self.__class__.__name__.lower() + "-raw.json"
            filepath = os.path.join("./data/", filename)
        
        f = open(filepath,'r')
        data = decode(f.read())
        return data

class Question(Model):
    def __init__(self):
        self.quest_bh = fake.ean(length=13)
        # 01 表示单选题 02 多选题 03 问答题
        self.quest_type = fake.random_element(["01","02","03"])
        self.quest_name = fake.sentence()
        self.daarray = [Option(), Option()]
        
class Option(object):
    def __init__(self):
        self.dabh = fake.ean(length=13)
        self.daname = fake.sentence()


class Revisit(Model):
    def __init__(self):
        self.returnvisit_content = fake.sentence()
        self.returnvisit_option = [RevisitOption()]
        
class RevisitOption(object):
    def __init__(self):
        self.option_id = fake.sentence()
        self.option_name = fake.sentence()
        
if __name__ == "__main__":
    question = Question()
    question.dump()
    # revisit = Revisit()
    # revisit.dump()
    
    raw_question = question.load()
    print(raw_question)
    print(raw_question.daarray)
