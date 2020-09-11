#!/bin/bash
model_name=bert-base-chinese-cls-cmnli
python ../../src/models/intent/test_sentence_similarity.py --model_name $model_name
