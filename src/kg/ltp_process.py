#coding=utf8

from ltp import LTP
import os

class LtpProcess():
    ###分词模型
    def __init__(self):
        path = os.path.join(os.path.realpath(os.path.dirname(__file__)), "..", "models", "ltp")
        self.ltp = LTP(path=path)

    def get_segmentor(self, question):
        arrs = []
        arrs.append(question)
        words, hidden  = self.ltp.seg(arrs)
        return words, hidden

    def get_postags(self, hidden):
        postags = self.ltp.pos(hidden)
        return postags 

if __name__ == '__main__':
    lp = LtpProcess()
    segment, hidden = lp.get_segmentor('差别电价指什么，我不太懂，能说说吗')
    postags = lp.get_postags(hidden)

    print(segment)
    print(postags)
