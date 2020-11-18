# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Natural language understanding."""

import collections
import re
import os
import logging
import math

from utils.str_process import expand_template, get_template_len, pattern_to_pinyin, strip_html_tags
from slot_filling import slots_filling, slots_status_init
from intent_recognition import IntentModelClassify, IntentModelTemplate, IntentModelSimilarity
from kg.search import KG
from kbqa.es import ES


class NLUManager(object):
    def __init__(self, intent_recognition_config, templates, intents, value_sets, stop_words, kb_config, kg_config):
        self.intent_recognition_config = intent_recognition_config
        self.templates = templates
        self.intents = intents
        self.value_sets = value_sets
        self.preprocess_value_sets()
        self.stop_words = stop_words
        self.kb_config = kb_config
        self.kg_config = kg_config

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
            logging.info(
                "config.bot.intent_recognition.classifier.on is set to False, no intent_model_classify loaded.")

        # intent_model_similarity
        self.similarity_conf = self.intent_recognition_config["similarity"]
        if self.similarity_conf["switch"]:
            similarity_model_path = os.path.join(os.path.dirname(__file__),
                                                 "models/sentence_encoder/sentence_transformers/checkpoints",
                                                 self.similarity_conf["model"])
            samples_embedding_path = "samples_embedding.pkl"
            if not os.path.exists(similarity_model_path):
                self.intent_model_similarity = None
                logging.info("No such directory: %s. No intent_model_classify loaded." % similarity_model_path)
            elif not os.path.exists(samples_embedding_path):
                self.intent_model_similarity = None
                logging.info("No such file: %s. No intent_model_classify loaded." % samples_embedding_path)
            else:
                self.intent_model_similarity = IntentModelSimilarity(model_path=similarity_model_path,
                                                                     samples_embedding_path=samples_embedding_path)
                logging.info("intent_model_similarity(%s) loaded." % self.similarity_conf["model"])
        else:
            self.intent_model_similarity = None
            logging.info(
                "config.bot.intent_recognition.similarity.on is set to False, no intent_model_similarity loaded.")

        # intent_model_template
        self.intent_model_template = IntentModelTemplate(self.templates)

        # kb
        index = self.kb_config["es"]["index_prefix"] + "_" + os.path.basename(os.getcwd())
        self.kb_module = ES(self.kb_config["es"]["addr"], index=index) if self.kb_config["switch"] else None
        logging.info("KBQA switch: %s" % self.kb_config["switch"])

        # kg
        self.kg_module = KG(self.kg_config["es"], self.kg_config["neo4j"]) if self.kg_config["switch"] else None
        logging.info("KG switch: %s" % self.kg_config["switch"])


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

    def qa_kb(self, user_utter):
        if self.kb_module is None:
            return None, None
        hit = self.kb_module.retrieve(user_utter)
        if hit is None:
            logging.info(f"KBQA(BM25): user_utter: '{user_utter}', hit_question: {{}}, score: 0")
            return None, None
        hit_question = hit["hit_question"]
        score = hit["score"]
        num_questions = hit["num_questions"]
        average_question_length = hit["average_question_length"]
        threshold = max(self.kb_config["threshold"] * math.log(1 + num_questions) * math.sqrt(average_question_length) * 0.33, 1.01)
        logging.info(f"KBQA(BM25): user_utter: '{user_utter}', hit_question: {hit_question}, score: {score}, threshold:{threshold}")
        if hit is None:
            return None, None
        if score < threshold:
            return None, None
        question = hit["doc"]["standard_question"]
        answer = hit["doc"]["answers"][0]
        recommend = ""
        if self.kb_config["recommend"]["switch"]:
            related_question_ids = hit["doc"]["related_questions"]
            related_question_docs = self.kb_module.query_by_ids(related_question_ids)[: self.kb_config["recommend"]["max_items"]]
            related_questions = [doc["_source"]["standard_question"] for doc in related_question_docs]
            if len(related_questions):
                recommend = "\n您是不是还想问：\n" + "\n".join(related_questions)
        response = f"{question}\n{answer}{recommend}"
        return response, hit

    def qa_kg(self, user_utter):
        if self.kg_module is None:
            return None
        es_search_results = self.kg_module.es_search(user_utter)
        q_id = None
        if len(es_search_results) > 0:
            label = es_search_results[0]["label"]
            score = es_search_results[0]["score"]
            logging.info("QA(KG): user_utter: %s, label: %s, score: %s" % (user_utter, label, score))
            if es_search_results[0]["score"] > self.kg_config["min_score"]:
                q_id = es_search_results[0]["id"]
            else:
                # todo: 加上log
                pass
        if q_id is None:
            return None
        neo4j_search_result = self.kg_module.neo4j_match_question_id(q_id)
        answer = neo4j_search_result.get('content', None)
        if type(answer) is str:
            answer = strip_html_tags(answer)
        if self.kg_config["recommend"]["switch"]:
            related_nodes = neo4j_search_result.get('related', [])
            recommend_questions = [node.get('label') for node in related_nodes if "label" in node]
            recommend_questions = recommend_questions[: self.kg_config["recommend"]["max_items"]]
            if len(recommend_questions):
                answer += "\n"
                answer += "您是不是还想问：\n" + "\n".join(recommend_questions)
        return answer

    def slots_filling(self, slots_status, user_utter, g_vars):
        return slots_filling(slots_status, user_utter, self.intents, self.value_sets, g_vars)

    def slots_status_init(self, slots):
        return slots_status_init(slots)


if __name__ == '__main__':
    pass
