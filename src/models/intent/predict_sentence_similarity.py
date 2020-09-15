import time
import json
import os
import sys
import csv
import random
import logging
import pickle
import time
import argparse
import shutil

import scipy.spatial
import numpy as np
import torch
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer
)

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from sentence_encoder.sentence_transformers.SentenceTransformer import SentenceTransformer


class SimilarityModel(object):
    def __init__(self, model_path, samples_embedding_path):
        # loading sentence similarity model
        self.model_path = model_path
        print('loading sentence similarity model: %s ...' % self.model_path)
        self.model = SentenceTransformer(self.model_path)
        self.model.eval()
        print("Done.")

        # get samples_embedding
        self.samples_embedding_path = samples_embedding_path
        print('loading samples embedding from: %s ...' % self.samples_embedding_path)
        with open(self.samples_embedding_path, "rb") as f:
            samples_embedding_dict = pickle.load(f)
            self.samples_embedding = samples_embedding_dict["embeddings"]
            self.samples = samples_embedding_dict["samples"]
            self.samples_label = samples_embedding_dict["labels"]
        print("Done.")

    @torch.no_grad()
    def predict(self, text):
        query_embeddings = self.model.encode([text])
        distances = scipy.spatial.distance.cdist(query_embeddings, self.samples_embedding, "cosine")[0]
        pred_idx = np.argmin(distances, axis=0)
        label = self.samples_label[pred_idx]
        sample = self.samples[pred_idx]
        similarity_max = 1 - distances[pred_idx]
        return label, sample, similarity_max


if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    model_path = "../../src/models/sentence_encoder/sentence_transformers/checkpoints/bert-base-chinese-mean-cmnli"
    samples_embedding_path = "samples_embedding.pkl"
    similarity_model = SimilarityModel(model_path=model_path, samples_embedding_path=samples_embedding_path)
    similarity_model.predict("测试")
    texts = ["查电费", "查一下电费", "电费", "抄表"]
    for text in texts:
        start = time.time()
        label, sample, similarity = similarity_model.predict(text)
        print(text, label, sample, similarity, time.time() - start)
