#!/bin/bash
task=intent
model_type=bert
pretrained_model_name_or_path=bert-base-chinese
model_class=bert
tokenizer_class=bert
ckpt_dir=checkpoints/$task/$model_type
data_dir=datasets/$task
rm -rf $ckpt_dir
rm -rf $data_dir

python ../../src/models/build_datasets.py

models_dir=../../src/models/
python $models_dir/train.py --task $task \
  --data_dir $data_dir \
  --output_dir $ckpt_dir \
  --pretrained_model_name_or_path $pretrained_model_name_or_path \
  --model_class $model_class \
  --tokenizer_class $tokenizer_class \
  --max_seq_length 64 \
  --batch_size 64 \
  --max_epochs 100 \
  --learning_rate 5e-5 \
  --warmup_prop 0.1 \
  --seed 12345

while true; do sleep 1; done