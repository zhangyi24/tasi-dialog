import sys
import os
import collections
import re
import logging

sys.path.append('..')
from models.bert.predict import Bert_Classifier


class IntentModel(object):
    def intent_recognition(self, user_utter):
        pass


class IntentModelTemplate(IntentModel):
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


class IntentModelBERT(IntentModel):
    def __init__(self, checkpoints_dir, label_dir):
        self.checkpoints_dir = checkpoints_dir
        self.label_dir = label_dir
        self.model = Bert_Classifier(checkpoints_dir=self.checkpoints_dir, label_dir=self.label_dir)

    def intent_recognition(self, user_utter):
        if not user_utter:
            intent_name, confidence = 'others', 1.0
        else:
            intent_name, confidence = self.model.predict([user_utter])[0]
            logging.info('intent recognition result(BERT): ("%s", %s, %s)' % (user_utter, intent_name, confidence))
            if confidence < 0.93:
                intent_name = 'others'
        intent_name = intent_name if intent_name != 'others' else None
        return intent_name
