python train_pl.py --data_dir intent \
  --task intent \
  --model_name_or_path bert-base-chinese \
  --output_dir intent-pl-bert \
  --max_seq_length 128 \
  --learning_rate 2e-5 \
  --num_train_epochs 3 \
  --train_batch_size 32 \
  --seed 2 \
  --do_train \
  --do_predict \
  --warmup_prop 0.1


while true; do sleep 2; done