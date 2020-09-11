"""
This is a simple application for sentence embeddings: semantic search

We have a corpus with various sentences. Then, for a given query sentence,
we want to find the most similar sentence in this corpus.

This script outputs for various queries the top 5 most similar sentences in the corpus.
"""
import os
import sys
import csv
import json
import random
import logging
import pickle
import time
import argparse
import shutil

import scipy.spatial
import numpy as np

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from sentence_encoder.sentence_transformers.SentenceTransformer import SentenceTransformer
from sentence_encoder.sentence_transformers import sentence_transformer_checkpoints_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", "-m", default="bert-base-chinese-mean-cmnli", type=str)
    parser.add_argument("--seed", "-s", default=12345, type=int)
    args = parser.parse_args()

    # get samples
    samples_path = 'dialog_config/corpus/samples.json'
    print('loading samples from: %s ...' % samples_path)
    with open(samples_path, 'r', encoding='utf-8') as f:
        samples_dict = json.load(f)
    samples = []
    labels = []
    for intent in samples_dict:
        samples.extend(samples_dict[intent]["samples"])
        labels.extend([intent] * len(samples))
    samples_embedding = {"embeddings": None, "samples": samples, "labels": labels}

    # load model
    model_path = os.path.join(sentence_transformer_checkpoints_path, args.model_name)
    print('loading model: %s ...' % args.model_name)
    model = SentenceTransformer(model_path)

    # encode samples
    print('encoding samples...')
    samples_embedding["embeddings"] = model.encode(samples, show_progress_bar=True)

    # save samples_embedding
    samples_embedding_pkl_path = 'samples_embedding.pkl'
    print("saving samples_embedding to %s ..." % samples_embedding_pkl_path)
    with open(samples_embedding_pkl_path, "wb") as f:
        pickle.dump(samples_embedding, f)
