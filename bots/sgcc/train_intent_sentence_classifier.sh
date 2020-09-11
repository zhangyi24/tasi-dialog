#!/bin/bash
model_type=bert
python ../../src/models/intent/train_sentence_classifier.py --model_type $model_type
