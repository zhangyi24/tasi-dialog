# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""BERT finetuning runner."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import collections
import csv
import random

import tensorflow as tf
import numpy as np

import modeling
import tokenization
import run_classifier


class Bert_Classifier(object):
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.task_name = 'intent'
        dir_name = os.path.dirname(__file__)
        self.bert_config_file = os.path.join(dir_name, 'chinese_L-12_H-768_A-12/bert_config.json')
        self.vocab_file = os.path.join(dir_name, 'chinese_L-12_H-768_A-12/vocab.txt')
        self.init_checkpoint = os.path.join(dir_name, 'chinese_L-12_H-768_A-12/bert_model.ckpt')
        self.model_dir = os.path.join(dir_name, 'new_data_tmp/intent')
        self.do_lower_case = True
        self.max_seq_length = 64
        self.predict_batch_size = 8

        tf.logging.set_verbosity(tf.logging.INFO)

        tokenization.validate_case_matches_checkpoint(self.do_lower_case, self.init_checkpoint)

        self.bert_config = modeling.BertConfig.from_json_file(self.bert_config_file)
        if self.max_seq_length > self.bert_config.max_position_embeddings:
            raise ValueError(
                "Cannot use sequence length %d because the BERT model "
                "was only trained up to sequence length %d" %
                (self.max_seq_length, self.bert_config.max_position_embeddings))

        task_name = self.task_name.lower()
        if task_name not in run_classifier.processors:
            raise ValueError("Task not found: %s" % (task_name))
        processor = run_classifier.processors[task_name](self.data_dir)
        self.label_list = processor.get_labels()

        self.tokenizer = tokenization.FullTokenizer(
            vocab_file=self.vocab_file, do_lower_case=self.do_lower_case)

        with tf.Graph().as_default():
            self.input_ids = tf.placeholder(shape=[None, self.max_seq_length], dtype=tf.int32)
            self.input_mask = tf.placeholder(shape=[None, self.max_seq_length], dtype=tf.int32)
            self.segment_ids = tf.placeholder(shape=[None, self.max_seq_length], dtype=tf.int32)
            self.label_ids = tf.placeholder(shape=[None], dtype=tf.int32)
            (_, _, _, self.probabilities) = run_classifier.create_model(
                bert_config=self.bert_config,
                is_training=False,
                input_ids=self.input_ids,
                input_mask=self.input_mask,
                segment_ids=self.segment_ids,
                labels=self.label_ids,
                num_labels=len(self.label_list),
                use_one_hot_embeddings=False)

            self.sess = tf.Session()
            self.sess.run(tf.global_variables_initializer())
            saver = tf.train.Saver()
            ckpt_dirs = []
            for file in os.listdir(self.model_dir):
                if file.startswith('model.ckpt-') and file.endswith('meta'):
                    ckpt_dirs.append(file[:-5])
            if not ckpt_dirs:
                print('No model found.')
            self.ckpt = os.path.join(self.model_dir, max(ckpt_dirs))
            saver.restore(self.sess, self.ckpt)

    def predict(self, texts):
        predict_examples = [run_classifier.InputExample(guid="", text_a=x, label=self.label_list[-1]) for x in texts]

        predict_features = run_classifier.convert_examples_to_features(predict_examples, self.label_list,
                                                                       self.max_seq_length,
                                                                       self.tokenizer)
        input_ids = []
        input_mask = []
        segment_ids = []
        label_ids = []
        for feature in predict_features:
            input_ids.append(feature.input_ids)
            input_mask.append(feature.input_mask)
            segment_ids.append(feature.segment_ids)
            label_ids.append(feature.label_id)
        input_ids = np.array(input_ids, dtype=np.int32)
        input_mask = np.array(input_mask, dtype=np.int32)
        segment_ids = np.array(segment_ids, dtype=np.int32)
        label_ids = np.array(label_ids, dtype=np.int32)

        probabilities = self.sess.run(fetches=(self.probabilities),
                                      feed_dict={
                                          self.input_ids: input_ids,
                                          self.input_mask: input_mask,
                                          self.segment_ids: segment_ids,
                                          self.label_ids: label_ids,
                                      })
        results = []
        for prob in probabilities:
            label_id = np.argmax(prob)
            results.append([self.label_list[label_id], label_id, prob])
        return results
