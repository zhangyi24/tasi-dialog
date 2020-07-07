import collections
import re
import os

from slot_filling import slots_filling, slots_status_init
from intent_recognition import IntentModelBERT, IntentModelTemplate


class NLUManager(object):
	def __init__(self, checkpoints_dir, label_dir, templates, intents, value_sets, stop_words):
		self.checkpoints_dir = checkpoints_dir
		self.label_dir = label_dir
		self.templates = templates
		self.precompile_templates()
		self.intents = intents
		self.value_sets = value_sets
		self.precompile_value_sets()
		self.stop_words = stop_words
		self.intent_model_bert = None
		if os.path.exists(self.checkpoints_dir) and os.path.exists(self.label_dir):
			self.intent_model_bert = IntentModelBERT(self.checkpoints_dir, self.label_dir)
		self.intent_model_template = IntentModelTemplate(self.templates)
	
	def precompile_templates(self):
		for intent_name in self.templates:
			for i, template in enumerate(self.templates[intent_name]['templates']):
				self.templates[intent_name]['templates'][i] = re.compile(template)
	
	def precompile_value_sets(self):
		for value_set_from in self.value_sets:
			for value_set in self.value_sets[value_set_from]:
				if self.value_sets[value_set_from][value_set]['type'] == 'regex':
					regex = self.value_sets[value_set_from][value_set]['regex']
					self.value_sets[value_set_from][value_set]['regex'] = re.compile(regex)
		
	def delete_stop_words(self, user_utter):
		for word in self.stop_words:
			user_utter = user_utter.replace(word, '')
		return user_utter
	
	def intent_recognition(self, user_utter):
		intent = None
		if self.intent_model_bert:
			intent = self.intent_model_bert.intent_recognition(user_utter)
		if not intent:
			intent = self.intent_model_template.intent_recognition(user_utter)
		return intent
	
	def slots_filling(self, slots_status, user_utter, g_vars):
		return slots_filling(slots_status, user_utter, self.intents, self.value_sets, g_vars)
	
	def slots_status_init(self, slots):
		return slots_status_init(slots)
	

if __name__ == '__main__':
	pass
