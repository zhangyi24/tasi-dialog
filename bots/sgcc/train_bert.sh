ckpt_dir=checkpoints/intent
data_dir=datasets/intent
bert_dir=../../src/models/bert
pretrained_ckpt_dir=$bert_dir/chinese_L-12_H-768_A-12
python ../../src/models/build_datasets.py

rm -rf $ckpt_dir

python $bert_dir/run_classifier.py \
  --task_name=intent \
  --do_train=true \
  --do_eval=true \
  --do_predict=true \
  --data_dir=$data_dir \
  --vocab_file=$pretrained_ckpt_dir/vocab.txt \
  --bert_config_file=$pretrained_ckpt_dir/bert_config.json \
  --init_checkpoint=$pretrained_ckpt_dir/bert_model.ckpt \
  --max_seq_length=64 \
  --train_batch_size=32 \
  --learning_rate=2e-5 \
  --num_train_epochs=10.0 \
  --output_dir=$ckpt_dir
