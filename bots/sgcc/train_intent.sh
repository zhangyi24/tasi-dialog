#!/bin/bash
model_type=bert
python ../../src/models/sentence_classifier/train_intent.py --model_type $model_type
