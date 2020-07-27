# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Intent recognition."""

import sys
import os
import collections
import re
import logging

sys.path.append('..')
from models.bert.predict import Bert_Classifier
from utils.str_process import expand_template, get_template_len, pattern_to_pinyin, hanzi_to_pinyin


class IntentModel(object):
    def intent_recognition(self, user_utter):
        pass


class IntentModelTemplate(IntentModel):
    def __init__(self, templates):
        self.templates = set()
        self.templates_info = {}
        for intent in templates:
            for template_raw in templates[intent]['templates']:
                for template in expand_template(template_raw):
                    self.templates.add(template)
                    template_pinyin = pattern_to_pinyin(template)
                    self.templates_info[template] = {
                        "intent": intent,
                        "regex": re.compile(template),
                        "template_pinyin": template_pinyin,
                        "regex_pinyin": re.compile(template_pinyin),
                        "template_raw": template_raw
                    }
        self.templates = list(self.templates)
        self.templates.sort(key=get_template_len, reverse=True)

    def intent_recognition(self, user_utter):
        result = None
        template_hit = None
        for template in self.templates:
            if self.templates_info[template]["regex"].search(user_utter):
                result = self.templates_info[template]["intent"]
                template_hit = template
                break
        if result:
            logging.info('intent recognition result(regex): (user_input: "%s", intent: %s, template: %s, template_raw: %s)' % (
            user_utter, result, template_hit, self.templates_info[template_hit]["template_raw"]))
        else:
            logging.info('intent recognition result(regex): (user_input: "%s", intent: %s)' % (user_utter, result))
        return result

    def intent_recognition_pinyin(self, user_utter):
        user_utter_pinyin, _ = hanzi_to_pinyin(user_utter)
        result = None
        template_hit = None
        for template in self.templates:
            if self.templates_info[template]["regex_pinyin"].search(user_utter_pinyin):
                result = self.templates_info[template]["intent"]
                template_hit = template
                break
        if result:
            logging.info('intent recognition result(regex_pinyin): (user_input: "%s", intent: %s, template: %s, template_raw: %s)' % (
            user_utter, result, template_hit, self.templates_info[template_hit]["template_raw"]))
        else:
            logging.info('intent recognition result(regex_pinyin): (user_input: "%s", intent: %s)' % (user_utter, result))
        return result


class IntentModelBERT(IntentModel):
    def __init__(self, checkpoints_dir):
        self.checkpoints_dir = checkpoints_dir
        self.model = Bert_Classifier(checkpoints_dir=self.checkpoints_dir)

    def intent_recognition(self, user_utter):
        if not user_utter:
            intent_name, confidence = None, 1.0
        else:
            intent_name, confidence = self.model.predict([user_utter])[0]
            logging.info('intent recognition result(BERT): ("%s", %s, %s)' % (user_utter, intent_name, confidence))
            if intent_name == 'others':
                intent_name = None
        return intent_name, confidence
