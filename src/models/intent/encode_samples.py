"""
This is a simple application for sentence embeddings: semantic search

We have a corpus with various sentences. Then, for a given query sentence,
we want to find the most similar sentence in this corpus.

This script outputs for various queries the top 5 most similar sentences in the corpus.
"""
import os
import sys
import json
import pickle

import yaml

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from sentence_encoder.sentence_transformers.SentenceTransformer import SentenceTransformer
from sentence_encoder.sentence_transformers import sentence_transformer_checkpoints_path

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
from utils.config import merge_config

if __name__ == '__main__':
    # builtin_conf
    builtin_config_file = os.path.join(os.path.dirname(__file__), "..", "..", 'config', 'config.yml')
    if os.path.exists(builtin_config_file):
        with open(builtin_config_file, 'r', encoding='utf-8') as f:
            conf = yaml.safe_load(f)

    # custom config
    custom_config_file_path = "config.yml"
    if os.path.exists(custom_config_file_path):
        with open(custom_config_file_path, 'r', encoding='utf-8') as f:
            custom_conf = yaml.safe_load(f)
    merge_config(conf, custom_conf)

    # get samples
    samples_path = 'dialog_config/corpus/samples.json'
    print('loading samples from: %s ...' % samples_path)
    with open(samples_path, 'r', encoding='utf-8') as f:
        samples_dict = json.load(f)
    samples = []
    labels = []
    for intent in samples_dict:
        samples_per_intent = samples_dict[intent]["samples"]
        samples.extend(samples_per_intent)
        labels.extend([intent] * len(samples_per_intent))
    samples_embedding = {"embeddings": None, "samples": samples, "labels": labels}

    # load model
    model_name = conf["bot"]["intent_recognition"]["similarity"]["model"]
    model_path = os.path.join(sentence_transformer_checkpoints_path, model_name)
    print('loading model: %s ...' % model_name)
    model = SentenceTransformer(model_path)

    # encode samples
    print('encoding samples...')
    samples_embedding["embeddings"] = model.encode(samples, batch_size=128, show_progress_bar=True)

    # save samples_embedding
    samples_embedding_pkl_path = 'samples_embedding.pkl'
    print("saving samples_embedding to %s ..." % samples_embedding_pkl_path)
    with open(samples_embedding_pkl_path, "wb") as f:
        pickle.dump(samples_embedding, f)
