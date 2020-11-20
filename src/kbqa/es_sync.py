#coding=utf-8

import json
import sys
import logging.config
import datetime
import os
import tqdm
import logging

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
        addr = conf["es"]["addr"]
        self.es = ES(addr)
        self.mysql_conf = conf["mysql"]
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
            self.last_sync_time = now

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

    logging.info("KBQA switch: %s" % conf_kb["switch"])
    if conf_kb["switch"]:
        tornado.ioloop.PeriodicCallback(synchonizer.sync_from_mysql, conf_kb["sync_period"] * 1000).start()  # start scheduler 每隔2s执行一次f2s
        logging.info('qa synchonizer started.')
        tornado.ioloop.IOLoop.current().start()
