import os
import logging

import jieba.posseg as pseg
from elasticsearch import Elasticsearch
import elasticsearch.helpers as es_helpers


class ES(object):
    def __init__(self, addr, recreate_index=False):
        self.addr = addr
        self.es = Elasticsearch(self.addr)
        es_root_path = self.get_es_root_path()
        self.synonyms_path_abs = os.path.join(es_root_path, "config/analysis/synonyms/kbqa.txt") if es_root_path else None
        if self.synonyms_path_abs:
            os.makedirs(os.path.dirname(self.synonyms_path_abs), exist_ok=True)
        self.settings = {
            "analysis": {
                "filter": {
                    "synonym": {
                        "type": "synonym",
                        "synonyms_path": self.synonyms_path_abs,
                        "updateable": True
                    }
                },
                "analyzer": {
                    "ik_max_word": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",
                    },
                    "ik_max_word_synonym": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",
                        "filter": ["synonym"] if self.synonyms_path_abs else []
                    }
                }
            }
        }
        self.mappings = {
            "kbqa_qa": {
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "standard_question": {
                        "type": "text"
                    },
                    "answers": {
                        "type": "text"
                    },
                    "category_id": {
                        "type": "keyword"
                    },
                    "is_published": {
                        "type": "keyword"
                    }
                }
            },
            "kbqa_questions": {
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "question": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_max_word_synonym"
                    },
                    "standard_question_id": {
                        "type": "keyword"
                    },
                    "is_standard": {
                        "type": "keyword"
                    }
                }
            },
            "kbqa_related_questions": {
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "standard_question_id": {
                        "type": "keyword"
                    },
                    "related_question_id": {
                        "type": "keyword"
                    }
                }
            },
            "kbqa_knowledge_categories": {
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "name": {
                        "type": "text"
                    }
                }
            },
            "kbqa_bots": {
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "name": {
                        "type": "text"
                    }
                }
            },
            "kbqa_categories_bots_mapping": {
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "category_id": {
                        "type": "keyword"
                    },
                    "bot_id": {
                        "type": "keyword"
                    }
                }
            }
        }
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return
        for index, mappings in self.mappings.items():
            if self.es.indices.exists(index=index) and recreate_index:
                self.es.indices.delete(index=index)
            if not self.es.indices.exists(index=index):
                self.es.indices.create(index=index, body={"settings": self.settings, "mappings": mappings})

    def get_es_root_path(self):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return None
        nodes_info = self.es.nodes.info()["nodes"]
        if not nodes_info:
            return None
        es_root_path = nodes_info.popitem()[1]["settings"]["path"]["home"]
        logging.info("es_root_path: %s" % es_root_path)
        return es_root_path

    def get_bot_id(self, bot_name):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return None
        index = "kbqa_bots"
        query_body = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"name": bot_name}}
                    ]
                }
            }
        }
        hits = self.es.search(body=query_body, index=index)["hits"]["hits"]
        return hits[0]["_source"]["id"] if hits else None

    def get_knowledge_category_ids(self, bot_name):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return []
        index = "kbqa_categories_bots_mapping"
        bot_id = self.get_bot_id(bot_name)
        if bot_id is None:
            return []
        query_body = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"bot_id": bot_id}}
                    ]
                }
            }
        }
        hits = self.es.search(body=query_body, index=index)["hits"]["hits"]
        return list(set(hit["_source"]["category_id"] for hit in hits))

    def get_standard_question_ids(self, bot_name):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return []
        index = "kbqa_qa"
        knowledge_category_ids = self.get_knowledge_category_ids(bot_name)
        query_body = {
            "query": {
                "bool": {
                    "filter": [
                        {"terms": {"category_id": knowledge_category_ids}},
                        {"term": {"is_published": 1}}
                    ]
                }
            }
        }
        hits = self.es.search(body=query_body, index=index)["hits"]["hits"]
        return list(set(hit["_source"]["id"] for hit in hits))

    def search_standard_question(self, query, cand_standard_question_ids, full=True, explain=True):
        if not query:
            return []
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return []
        index = "kbqa_questions"
        field = "question"
        if full:
            query_body_core = {
                "match_phrase": {
                    field: {
                        "query": query,
                        "slop": 10
                    }
                }
            }
        else:
            should = []
            for word, postag in pseg.cut(query):
                if postag[0].lower() in ["n", "v"]:
                    should.append({
                        "match_phrase": {
                            field: {
                                "query": word,
                                "slop": 2
                            }
                        }
                    })
            if not should:
                return []
            query_body_core = {
                "bool": {
                    "should": should
                }
            }
        query_body = {
            "query": {
                "bool": {
                    "must":  query_body_core,
                    "filter": [
                        {"terms": {"standard_question_id": cand_standard_question_ids}},
                    ]
                }
            }
        }
        hits = self.es.search(body=query_body, index=index, explain=explain)["hits"]["hits"]
        return hits

    def get_qa(self, standard_question_id):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return None
        index = "kbqa_qa"
        try:
            qa = self.es.get(index, standard_question_id)["_source"]
        except Exception as e:
            logging.info(e)
            qa = {}
        return qa

    def get_related_question_ids(self, standard_question_id):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return []
        index = "kbqa_related_questions"
        query_body = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"standard_question_id": standard_question_id}},
                    ]
                }
            }
        }
        hits = self.es.search(body=query_body, index=index)
        return list(set(hit["_source"]["related_question_id"] for hit in hits["hits"]["hits"]))

    def get_related_questions(self, related_question_ids):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return []
        index = "kbqa_qa"
        query_body = {
            "query": {
                "bool": {
                    "filter": [
                        {"terms": {"id": related_question_ids}},
                        {"term": {"is_published": 1}}
                    ]
                }
            }
        }
        hits = self.es.search(body=query_body, index=index)["hits"]["hits"]
        related_questions = [hit["_source"]["standard_question"] for hit in hits]
        return related_questions

    def retrieve(self, query, bot_name, explain=True):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return None
        cand_standard_question_ids = self.get_standard_question_ids(bot_name)
        hits = self.search_standard_question(query, cand_standard_question_ids, explain=explain)
        if not hits:
            hits = self.search_standard_question(query, cand_standard_question_ids, full=False, explain=explain)
            if not hits:
                return None
        hit = hits[0]
        num_docs = self.get_num_docs(hit["_explanation"])
        avg_len = self.get_avg_len(hit["_explanation"])
        hit_standard_question_id = hit["_source"]['standard_question_id']
        qa = self.get_qa(hit_standard_question_id)
        related_question_ids = self.get_related_question_ids(hit_standard_question_id)
        related_questions = self.get_related_questions(related_question_ids)
        return {"score": hit["_score"],
                "hit_question": hit["_source"],
                "qa": qa,
                "related_questions": related_questions,
                "num_questions": num_docs,
                "average_question_length": avg_len}

    def ping(self):
        try:
            ping_result = self.es.ping()
        except Exception as e:
            ping_result = False
        return ping_result

    def get_ids(self, index):
        if not self.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.addr}")
            return []
        hits = es_helpers.scan(client=self.es, query={"query": {"match_all": {}}, "_source": ["id"]}, index=index)
        return [doc["_source"]["id"] for doc in hits]

    def get_num_docs(self, explanation):
        for child in explanation["details"]:
            value_child = self.get_num_docs(child)
            if value_child is not None:
                return value_child
        return explanation["value"] if explanation["description"] == "N, total number of documents with field" else None

    def get_avg_len(self, explanation):
        for child in explanation["details"]:
            value_child = self.get_avg_len(child)
            if value_child is not None:
                return value_child
        return explanation["value"] if explanation["description"] == "avgdl, average length of field" else None


if __name__ == "__main__":
    address = 'http://127.0.0.1:9200'
    es = ES(address)
    print(es.get_ids("kbqa_qa"))
