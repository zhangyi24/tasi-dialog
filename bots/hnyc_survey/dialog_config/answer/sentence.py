from sentence_transformers import SentenceTransformer, util
import torch
from time import time
import jieba

class Timer(object):
    def __init__(self, description):
        self.description = description
    def __enter__(self):
        self.start = time()
    def __exit__(self, type, value, traceback):
        self.end = time()
        print(f"{self.description}: {self.end - self.start}")

with Timer("Load Model"):
    model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')

def embedding(sentences):
    sentence_embeddings = model.encode(sentences)
    for sentence, embedding in zip(sentences, sentence_embeddings):
        print("Sentence:", sentence)
        print("Embedding:", embedding)
        print("")
        
def distance(sentences, answer):
    print(f"{answer} in {sentences}")
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    answer_embeddings = model.encode([answer], convert_to_tensor=True)
    #Compute cosine-similarities for each sentence with each other sentence
    cosine_scores = util.pytorch_cos_sim(sentence_embeddings, answer_embeddings)
    index = torch.argmax(cosine_scores)
    print(f"{answer} -> {sentences[index]}, {cosine_scores}")
    return sentences[index]

def cut(sentences):
    for text in sentences:
        seg_list = jieba.cut(text, cut_all=False) 
        print("Full Mode: " + " ".join(seg_list))

def test_answer():
    sentences1 = ['很满意','基本满意','不满意']
    answer1 = ['狠满意','太烂了','牛逼上天了','烂透了','马马虎虎']
    for ans in answer1:
        with Timer(f"Calculate {ans}"):
            distance(sentences1, ans)

#cut(sentences1)
