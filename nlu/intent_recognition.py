import sys
import os
import collections
import re
import logging

sys.path.append('..')
from model.bert.predict import Bert_Classifier


class NLU_Model(object):
	def intent_recognition(self, user_utter):
		pass


class NLU_Model_template(NLU_Model):
	def __init__(self, templates):
		self.templates = templates

	def intent_recognition(self, user_utter):
		result = None
		for intent_name in self.templates:
			for template in self.templates[intent_name]['templates']:
				if template.search(user_utter):
					result = intent_name
					break
		logging.info('intent recognition result(regex): ("%s", %s)' % (user_utter, result))
		return result


class NLU_Model_bert(NLU_Model):
	def __init__(self):
		data_dir = os.path.dirname(__file__)
		data_dir = os.path.join(data_dir, '../datasets/intent_recognition')
		self.model = Bert_Classifier(data_dir=data_dir)

	def intent_recognition(self, user_utter):
		intent_name = self.model.predict([user_utter])[0][0] if user_utter else 'others'
		intent_name = intent_name if intent_name != 'others' else None
		logging.info('intent recognition result(BERT): ("%s", %s)' % (user_utter, intent_name))
		return intent_name
