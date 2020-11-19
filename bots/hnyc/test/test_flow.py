import unittest
from server_text import initbot
import re,glob,os

class TestFlow(unittest.TestCase):
    def setUp(self):
        bot, conf = initbot()
        self.bot = bot
        self.conf = conf
        self.user_id = 1
        self.bot.init(self.user_id, {}, None, -1)
        
    # def test_greeting(self):
    #     print(f"{self.bot.users}")
    #     resp, status = self.bot.greeting(user_id=self.user_id)
    #     print(f"resp={resp}.status={status}")
    #
    # def test_response(self):
    #     input = "我要订货"
    #     resp, status = self.bot.response(self.user_id, input)
    #     print(f"resp={resp}.status={status}")

def test_flow_generator(filepath):
    f = open(filepath, 'r') 
    lines = f.readlines()
    lines = [re.sub("^bot:[\t ]*|^user:[\t ]*|\n",'',l) for l in lines]
    def test(self):
        resp, status = self.bot.greeting(user_id=self.user_id)
        greeting = lines.pop(0)
        self.assertEqual(resp['content'], greeting, msg="Greeting failed")
        for i in range(0, int(len(lines)/2)):
            ask = lines.pop(0)
            response = lines.pop(0)
            resp, status = self.bot.response(self.user_id, ask)
            line_index = i*2 + 3
            self.assertEqual(resp['content'], response, msg=f"Response at line {line_index} failed")
    return test

case_dir = os.path.realpath(os.path.realpath(__file__) + '/../cases/*.txt')
for f in glob.glob(case_dir):
    test_name = 'test_flow_%s' % os.path.basename(f)
    test = test_flow_generator(f)
    setattr(TestFlow, test_name, test)

    
    