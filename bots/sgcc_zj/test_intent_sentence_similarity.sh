#!/bin/bash
model_name=bert-base-chinese-mean-cmnli
python ../../src/models/intent/test_sentence_similarity.py --model_name $model_name
