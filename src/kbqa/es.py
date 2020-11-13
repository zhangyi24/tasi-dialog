import json
import codecs
import sys
import os
import logging

import jieba.posseg as pseg
import tqdm
from elasticsearch import Elasticsearch


class ES(object):
    def __init__(self, address, index, synonyms=None):
        self.address = address
        self.index = index
        self.es = Elasticsearch(self.address)
        if synonyms is None:
            synonyms = []
        self.index_settings = {
            "settings": {
                "analysis": {
                    "filter": {
                        "synonym": {
                            "type": "synonym",
                            "synonyms": synonyms
                        }
                    },
                    "analyzer": {
                        "ik_max_word_synonym": {
                            "type": "custom",
                            "tokenizer": "ik_max_word",
                            "filter": ["synonym"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "standard_question": {
                        "type": "text",
                        "analyzer": "ik_max_word_synonym"
                    },
                    "questions": {
                        "type": "nested",
                        "properties": {
                            "question": {
                                "type": "text",
                                "analyzer": "ik_max_word_synonym"
                            },
                            "is_standard": {
                                "type": "boolean"
                            },
                            "id": {
                                "type": "keyword"
                            }
                        }
                    },
                    "related_questions": {
                        "type": "text"
                    },
                    "answers": {
                        "type": "text"
                    },
                    "id": {
                        "type": "keyword"
                    }
                }
            }
        }
        if not self.es.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.address}")
            return
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index, body=self.index_settings)

    def index_doc(self, file):
        if not self.es.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.address}")
            return
        if self.es.indices.exists(index=self.index):
            res = self.es.indices.delete(index=self.index)
            # print(f"indices_delete result: {res}")
        result = self.es.indices.create(index=self.index, body=self.index_settings)
        # print(f"indices_create result: {result}")
        # 添加索引
        items = []
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                items = json.load(f)
        for item in tqdm.tqdm(items, desc="indexing qa"):
            item["questions"] = item.pop("similar_questions")
            questions = item["questions"]
            for question in questions:
                question["is_standard"] = False
            item["questions"].append({"question": item["standard_question"], "is_standard": True, "id": item["id"]})
            res = self.es.index(index=self.index, body=item, id=item["id"])
            # print(f"index result: {res}")
        self.es.indices.refresh(index=self.index)
        # print(self.es.search(body={"query": {"match_all": {}}}, index=es.index))
        # print(self.es.get(id="0",index=self.index))
        # success, _ = bulk(es, ACTIONS, index=index, raise_on_error=True)

    def retrieve(self, query, explain=True):
        if not self.es.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.address}")
            return None
        try:
            hits = self.search(query, explain=explain)
            if not hits["hits"]["hits"]:
                try:
                    hits = self.search(query, full=False, explain=explain)
                except Exception as e:
                    print(e)
                    return None
            hits = hits["hits"]["hits"]
            if not hits:
                return None
            else:
                hit = hits[0]
                num_questions, avgdl = self.get_num_questions_and_avgdl(hit["_explanation"])
                return {"score": hit["_score"],
                        "hit_question": hit["inner_hits"]["questions"]["hits"]["hits"][0]["_source"],
                        "doc": hit["_source"],
                        "num_questions": num_questions,
                        "average_question_length": avgdl}
        except Exception as e:
            print(e)
            return None

    def search(self, query, full=True, explain=True):
        field = "questions.question"
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
            query_body_core = {
                "bool": {
                    "should": should
                }
            }
        query_body = {
            "query": {
                "nested": {
                    "path": "questions",
                    "query": query_body_core,
                    "score_mode": "max",
                    "inner_hits": {}
                }
            }
        }
        hits = self.es.search(body=query_body, index=self.index, explain=explain)
        return hits

    def get_num_questions(self):
        agg_body = {
            "size": 0,
            "aggs": {
                "cnt_questions": {
                    "sum": {
                        "script": {
                            "source": "params._source.questions.size()"
                        }
                    }
                }
            }
        }
        agg_result = self.es.search(body=agg_body, index=self.index)
        return agg_result['aggregations']['cnt_questions']['value']

    def get_num_questions_and_avgdl(self, explanation):
        idf = explanation["details"][0]["details"][0]["details"][0]["details"][1]["details"]
        tf = explanation["details"][0]["details"][0]["details"][0]["details"][2]["details"]
        num_docs = idf[0]["details"][1]["value"]
        avgdl = tf[4]["value"]
        return num_docs, avgdl


if __name__ == "__main__":
    address = 'http://127.0.0.1:9200'
    index = 'qa'

    es = ES(address, index)
    # es.index_doc("kb.json")
    # es.search("类似问")
    es.search("类似问的", full=False)

