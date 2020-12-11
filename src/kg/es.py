# coding=utf-8
from elasticsearch import Elasticsearch
import os, json, codecs, sys, logging

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


class ElasticSearch(object):
    def __init__(self, address, index, table):
        self.address = address
        self.index = index
        self.table = table
        self.es = Elasticsearch(self.address)

    def search(self, key):
        shoulds = []
        # todo: 了解query
        if isinstance(key, list):
            for word in key:
                tmp = {
                    "match_phrase": {
                        "label": {
                            "query": word,
                            "slop": 2,
                            "boost": 1.0
                        }
                    }
                }
                shoulds.append(tmp)
            query = {
                "query": {
                    "bool": {
                        "should": shoulds
                    }
                }
            }

        else:
            query = {
                "query": {
                    "match_phrase": {
                        "label": {
                            "query": key,
                            "slop": 10,
                            "boost": 1.0
                        }
                    }
                }
            }
        arrs = []
        try:
            res = self.es.search(index=self.index, body=query)
            res = res.get('hits').get('hits')
            for data in res:
                source = data.get('_source')
                label = source.get('label')
                _id = source.get('id')
                score = data.get('_score')
                tmp = {}
                tmp = {'score': score, 'label': label, 'id': _id}
                arrs.append(tmp)
        except Exception as e:
            logging.info(e)
            logging.info('error')

        return arrs
