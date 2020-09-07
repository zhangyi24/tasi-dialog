#!/bin/bash
model_type=bert
python ../../src/models/train_intent.py --model_type $model_type \
  --batch_size 64

while true; do sleep 1; done
