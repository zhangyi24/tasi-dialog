python train.py --data_dir intent \
  --task intent \
  --model_name_or_path bert-base-chinese \
  --model_type bert \
  --tokenizer_type bert \
  --output_dir intent-pl-bert \
  --max_seq_length 64 \
  --learning_rate 2e-5 \
  --num_train_epochs 1 \
  --train_batch_size 64 \
  --seed 12345 \
  --do_train \
  --do_predict \
  --warmup_prop 0.1


while true; do sleep 2; done