#coding=utf-8

from .es import ElasticSearch
from .neo4j import Neo4j
from .ltp_process import LtpProcess


class KG(object):
    def __init__(self, es_config, neo4j_config):
        self.es = ElasticSearch(**es_config)
        self.neo4j = Neo4j(**neo4j_config)
        self.ltp = LtpProcess()

    def es_search(self, query):
        # todo:搞一搞逻辑
        results = self.es.search(query)
        if len(results) == 0:
            words, hidden = self.ltp.get_segmentor(query)
            postags = self.ltp.get_postags(hidden)
            words = words[0]
            postags = postags[0]
            keys = []
            for num in range(len(words)):
                postag = postags[num]
                if postag == 'n':
                    keys.append(words[num])
            results = self.es.search(keys)
        return results

    def neo4j_match_question_id(self, question_id):
        #neo4j标准问对应答案查询
        result = self.neo4j.matchQuestionbyId(question_id)
        return result

