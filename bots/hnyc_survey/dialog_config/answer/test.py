# import nltk
# nltk.download('wordnet_ic')
#
from harvesttext import HarvestText
ht = HarvestText()

text = ["满意,十分满意,特别满意"]

def jieba(text):
    kwds = ht.extract_keywords(text, 5, method="jieba_tfidf")
    return kwds
    
def textrank(text):
    kwds = ht.extract_keywords(text, 5, method="textrank")
    return kwds
    

# for t in text:
#     print("textrank", jieba(t))
#

import jieba
import jieba.analyse
 
sentence = '满意,十分满意,特别满意'
 
text = "烟草公司会议,客户经理宣传,其它零售户的介绍"

keywords = jieba.analyse.extract_tags(text, topK=20, withWeight=True, allowPOS=('n','nr','ns'))
 
print(keywords)
# <class 'list'>
 
for item in keywords:
    print(item[0],item[1])