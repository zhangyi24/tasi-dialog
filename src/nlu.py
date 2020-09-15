# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Natural language understanding."""

import collections
import re
import os
import logging

from utils.str_process import expand_template, get_template_len, pattern_to_pinyin
from slot_filling import slots_filling, slots_status_init
from intent_recognition import IntentModelClassify, IntentModelTemplate, IntentModelSimilarity


class NLUManager(object):
	def __init__(self, intent_recognition_config, templates, intents, value_sets, stop_words):
		self.intent_recognition_config = intent_recognition_config
		self.templates = templates
		self.intents = intents
		self.value_sets = value_sets
		self.preprocess_value_sets()
		self.stop_words = stop_words

		# intent_model_classify
		self.classifier_conf = self.intent_recognition_config["classifier"]
		if self.classifier_conf["switch"]:
			intent_model_classify_path = 'checkpoints/intent/%s/best_model' % self.classifier_conf["model"]
			if os.path.exists(intent_model_classify_path):
				self.intent_model_classify = IntentModelClassify(intent_model_classify_path)
				logging.info("intent_model_classify(%s) loaded." % self.classifier_conf["model"])
			else:
				self.intent_model_classify = None
				logging.info("No such directory: %s. No intent_model_classify loaded." % intent_model_classify_path)
		else:
			self.intent_model_classify = None
			logging.info("config.bot.intent_recognition.classifier.on is set to False, no intent_model_classify loaded.")

		# intent_model_similarity
		self.similarity_conf = self.intent_recognition_config["similarity"]
		if self.similarity_conf["switch"]:
			similarity_model_path = os.path.join(os.path.dirname(__file__), "models/sentence_encoder/sentence_transformers/checkpoints", self.similarity_conf["model"])
			samples_embedding_path = "samples_embedding.pkl"
			if not os.path.exists(similarity_model_path):
				self.intent_model_similarity = None
				logging.info("No such directory: %s. No intent_model_classify loaded." % similarity_model_path)
			elif not os.path.exists(samples_embedding_path):
				self.intent_model_similarity = None
				logging.info("No such file: %s. No intent_model_classify loaded." % samples_embedding_path)
			else:
				self.intent_model_similarity = IntentModelSimilarity(model_path=similarity_model_path, samples_embedding_path=samples_embedding_path)
				logging.info("intent_model_similarity(%s) loaded." % self.similarity_conf["model"])
		else:
			self.intent_model_similarity = None
			logging.info("config.bot.intent_recognition.similarity.on is set to False, no intent_model_similarity loaded.")

		# intent_model_template
		self.intent_model_template = IntentModelTemplate(self.templates)

	def preprocess_value_sets(self):
		"""1.编译regex型的正则表达式。2.把dict型的别名按长度从长到短排序"""
		for value_set_from in self.value_sets:
			for value_set_name in self.value_sets[value_set_from]:
				if self.value_sets[value_set_from][value_set_name]['type'] == 'regex':
					regex = self.value_sets[value_set_from][value_set_name]['regex']
					self.value_sets[value_set_from][value_set_name]['regex'] = re.compile(regex)
				elif self.value_sets[value_set_from][value_set_name]['type'] == 'dict':
					value_set = self.value_sets[value_set_from][value_set_name]
					value_set["templates"] = set()
					value_set["templates_info"] = dict()
					for standard_value, templates_raw in value_set['dict'].items():
						for template_raw in templates_raw:
							for template in expand_template(template_raw):
								template_pinyin = pattern_to_pinyin(template)
								value_set["templates"].add(template)
								value_set["templates_info"][template] = {
									"standard_value": standard_value,
									"regex": re.compile(template),
									"template_pinyin": template_pinyin,
									"regex_pinyin": re.compile(template_pinyin),
									"template_raw": template_raw
								}
					value_set["templates"] = list(value_set["templates"])
					value_set["templates"].sort(key=get_template_len, reverse=True)
		
	def delete_stop_words(self, user_utter):
		for word in self.stop_words:
			user_utter = user_utter.replace(word, '')
		return user_utter
	
	def intent_recognition(self, user_utter):
		intent = None
		# 多分类模型
		if self.intent_model_classify:
			intent, confidence = self.intent_model_classify.intent_recognition(user_utter)
			if confidence < self.classifier_conf['min_confidence']:
				intent = None
		# 模板匹配
		if not intent:
			intent = self.intent_model_template.intent_recognition(user_utter)
		# 模板拼音匹配
		if not intent:
			intent = self.intent_model_template.intent_recognition_pinyin(user_utter)
		# 相似度模型
		if self.intent_model_similarity and not intent:
			intent, similarity = self.intent_model_similarity.intent_recognition(user_utter)
			if similarity < self.similarity_conf['min_similarity']:
				intent = None
		return intent
	
	def slots_filling(self, slots_status, user_utter, g_vars):
		return slots_filling(slots_status, user_utter, self.intents, self.value_sets, g_vars)

	def slots_status_init(self, slots):
		return slots_status_init(slots)
	

if __name__ == '__main__':
	pass
