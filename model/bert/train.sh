python run_classifier.py --task_name=intent --do_train=true --do_eval=true --do_predict=true --data_dir=../../datasets/intent_recognition --vocab_file=chinese_L-12_H-768_A-12/vocab.txt --bert_config_file=chinese_L-12_H-768_A-12/bert_config.json --init_checkpoint=chinese_L-12_H-768_A-12/bert_model.ckpt --max_seq_length=64 --train_batch_size=32 --learning_rate=2e-5 --num_train_epochs=6.0 --output_dir=./new_data_tmp/intent/