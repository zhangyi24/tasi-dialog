# coding=utf-8

import json
import sys
import logging.config
import datetime
import os
import tqdm
import logging
import collections

import tornado.ioloop
import tornado.web
import yaml
import mysql.connector
import mysql.connector.pooling

from es import ES

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from utils.config import merge_config
from utils.logger import config_logger


class Synchonizer(object):
    def __init__(self, conf):
        addr = "http://127.0.0.1:%s" % conf["es"]["port"]
        self.es = ES(addr, recreate_index=True)
        self.mysql_conf = conf["sync"]["mysql"]
        self.last_sync_time = datetime.datetime(1970, 1, 1)

    def sync_mysql_table(self, cnx, table, now):
        index = table
        logging.info(f"sync data from mysql table '{table}' to elasticsearch index '{index}'")
        index = table
        ids_es = set(self.es.get_ids(index=table))
        with cnx.cursor(dictionary=True) as cursor:
            query = f"SELECT * FROM {table}"
            cursor.execute(query)
            cnt = {"add": 0, "update": 0, "remain": 0, "delete": 0}
            for item in tqdm.tqdm(cursor, desc="indexing doc"):
                if item["id"] in ids_es:
                    ids_es.remove(item["id"])
                    if self.last_sync_time < item["update_time"] <= now:
                        cnt["update"] += 1
                        self.index_record(index, item)
                    else:
                        cnt["remain"] += 1
                else:
                    cnt["add"] += 1
                    self.index_record(index, item)
            cnt["delete"] = len(ids_es)
            for doc_id in tqdm.tqdm(ids_es, desc="deleting doc"):
                self.es.es.delete(index=index, id=doc_id)
            self.es.es.indices.refresh(index=index)
            logging.info("add: %d, update: %d, remain %d, delete: %d" % (
                cnt["add"], cnt["update"], cnt["remain"], cnt["delete"]))

    def sync_from_mysql(self):
        if not self.es.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.es.addr}")
            return
        with mysql.connector.connect(**self.mysql_conf) as cnx:
            if not cnx.is_connected():
                logging.info(f"Can't connect to MySQL server on : {self.mysql_conf['host']}:{self.mysql_conf['port']}")
                return
            now = datetime.datetime.now()
            for table in self.es.mappings:
                self.sync_mysql_table(cnx, table, now)
            self.sync_synonyms(cnx)
            self.last_sync_time = now

    def sync_synonyms(self, cnx):
        index = "kbqa_questions"
        synonym_map = collections.defaultdict(set)
        with cnx.cursor(dictionary=True) as cursor:
            query = "SELECT c.word as core_word, s.synonym as synonym, c.update_time as coreword_update_time, s.update_time as synonym_update_time FROM kbqa_corewords as c INNER JOIN kbqa_synonyms as s ON c.id = s.coreword_id"
            cursor.execute(query)
            for record in cursor:
                synonym_map[record["core_word"]].add(record["synonym"])
        if self.es.synonyms_path_abs:
            os.makedirs(os.path.dirname(self.es.synonyms_path_abs), exist_ok=True)
            with open(self.es.synonyms_path_abs, "w", encoding="utf-8") as f:
                for coreword, synonyms in synonym_map.items():
                    line = ", ".join([coreword] + list(synonyms))
                    print(line, file=f)
            logging.info(self.es.es.indices.reload_search_analyzers(index))
            self.es.es.indices.refresh(index=index)


    def index_record(self, index, record):
        self.es.es.index(index=index, body=record, id=record["id"])


if __name__ == "__main__":
    # config logger
    config_logger('logs/qa_synchronize')

    # default config
    default_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yml')
    if os.path.exists(default_config_file):
        with open(default_config_file, 'r', encoding='utf-8') as f:
            conf = yaml.safe_load(f)
    conf_kb = conf["bot"]["kb"]

    synchonizer = Synchonizer(conf_kb)
    synchonizer.sync_from_mysql()

    logging.info("KBQA switch: %s" % conf_kb["switch"])
    tornado.ioloop.PeriodicCallback(synchonizer.sync_from_mysql,
                                    conf_kb["sync"]["period"] * 1000).start()  # start scheduler 每隔2s执行一次f2s
    logging.info('qa synchonizer started.')
    tornado.ioloop.IOLoop.current().start()
