import collections
import re

from .slot_filling import slots_filling, slots_status_init
from .intent_recognition import NLU_Model_bert, NLU_Model_template


class NLUManager(object):
	def __init__(self, templates, intents, entities, stop_words):
		self.templates = templates
		self.re_precompile_templates()
		self.intents = intents
		self.entities = entities
		self.re_precompile_entities()
		self.stop_words = stop_words
		self.nlu_model_bert = NLU_Model_bert()
		self.nlu_model_template = NLU_Model_template(self.templates)
	
	def re_precompile_templates(self):
		for intent_name in self.templates:
			for i, template in enumerate(self.templates[intent_name]['templates']):
				self.templates[intent_name]['templates'][i] = re.compile(template)
	
	def re_precompile_entities(self):
		for entity_from in self.entities:
			for entity in self.entities[entity_from]:
				if self.entities[entity_from][entity]['type'] == 'regex':
					regex = self.entities[entity_from][entity]['regex']
					self.entities[entity_from][entity]['regex'] = re.compile(regex)
		
	def delete_stop_words(self, user_utter):
		for word in self.stop_words:
			user_utter = user_utter.replace(word, '')
		return user_utter
	
	def intent_recognition(self, user_utter):
		intent = self.nlu_model_bert.intent_recognition(user_utter)
		if not intent:
			intent = self.nlu_model_template.intent_recognition(user_utter)
		return intent
	
	def slots_filling(self, slots, user_utter, g_vars):
		return slots_filling(slots, user_utter, self.intents, self.entities, g_vars)
	
	def slots_status_init(self, slots_status, user_utter, g_vars):
		return slots_status_init(slots_status, user_utter, self.intents, self.entities, g_vars)
	

if __name__ == '__main__':
	pass
