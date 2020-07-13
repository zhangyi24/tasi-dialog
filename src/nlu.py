import collections
import re
import os

from slot_filling import slots_filling, slots_status_init
from intent_recognition import IntentModelBERT, IntentModelTemplate


class NLUManager(object):
	def __init__(self, checkpoints_dir, templates, intents, value_sets, stop_words, thresholds):
		self.checkpoints_dir = checkpoints_dir
		self.templates = templates
		self.preprocess_templates()
		self.intents = intents
		self.value_sets = value_sets
		self.preprocess_value_sets()
		self.stop_words = stop_words
		self.thresholds = thresholds
		self.intent_model_bert = None
		if os.path.exists(self.checkpoints_dir):
			self.intent_model_bert = IntentModelBERT(self.checkpoints_dir)
		self.intent_model_template = IntentModelTemplate(self.templates)
	
	def preprocess_templates(self):
		for intent_name in self.templates:
			for i, template in enumerate(self.templates[intent_name]['templates']):
				self.templates[intent_name]['templates'][i] = re.compile(template)
	
	def preprocess_value_sets(self):
		"""1.编译正则表达式。2.把dict型的别名按长度从长到短排序"""
		for value_set_from in self.value_sets:
			for value_set_name in self.value_sets[value_set_from]:
				if self.value_sets[value_set_from][value_set_name]['type'] == 'regex':
					regex = self.value_sets[value_set_from][value_set_name]['regex']
					self.value_sets[value_set_from][value_set_name]['regex'] = re.compile(regex)
				elif self.value_sets[value_set_from][value_set_name]['type'] == 'dict':
					values = set()
					reverse_idx = {}
					for standard_value_name, aliases in self.value_sets[value_set_from][value_set_name]['dict'].items():
						for alias in aliases:
							values.add(alias)
							reverse_idx[alias] = standard_value_name
					values = list(values)
					values.sort(key=len, reverse=True)
					self.value_sets[value_set_from][value_set_name]['values_sorted'] = values
					self.value_sets[value_set_from][value_set_name]['reverse_idx'] = reverse_idx
		
	def delete_stop_words(self, user_utter):
		for word in self.stop_words:
			user_utter = user_utter.replace(word, '')
		return user_utter
	
	def intent_recognition(self, user_utter):
		intent = None
		if self.intent_model_bert:
			intent, confidence = self.intent_model_bert.intent_recognition(user_utter)
			if confidence < self.thresholds['intent_bert']:
				intent = None
		if not intent:
			intent = self.intent_model_template.intent_recognition(user_utter)
		return intent
	
	def slots_filling(self, slots_status, user_utter, g_vars):
		return slots_filling(slots_status, user_utter, self.intents, self.value_sets, g_vars)
	
	def slots_status_init(self, slots):
		return slots_status_init(slots)
	

if __name__ == '__main__':
	pass
