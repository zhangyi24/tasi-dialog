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
        bot_name = os.path.basename(os.getcwd())
        self.index = conf["es"]["index_prefix"] + "_" + bot_name
        synonyms_path = os.path.abspath(os.path.realpath("qa/synonym.txt"))
        synonyms = []
        if os.path.exists(synonyms_path):
            with open(synonyms_path, "r", encoding="utf-8") as f:
                synonyms = f.read().strip().split("\n")
        logging.info(f"synonyms: {synonyms}")
        self.es = ES(addr, self.index, synonyms)
        self.mysql_conf = conf["mysql"]
        self.last_sync_time = datetime.datetime(1970, 1, 1)

    def sync_from_mysql(self):
        if not self.es.ping():
            logging.info(f"Can not connect to elasticsearch cluster: {self.es.addr}")
            return
        with mysql.connector.connect(**self.mysql_conf) as cnx:
            if not cnx.is_connected():
                logging.info(f"Can't connect to MySQL server on : {self.mysql_conf['host']}:{self.mysql_conf['port']}")
                return
            now = datetime.datetime.now()
            ids_es = set(self.es.get_ids())
            with cnx.cursor(dictionary=True) as cursor:
                query = f"SELECT * FROM {self.index}"
                cursor.execute(query)
                cnt = {"add": 0, "update": 0, "remain": 0, "delete": 0}
                for item in tqdm.tqdm(cursor, desc="indexing doc"):
                    if item["id"] in ids_es:
                        ids_es.remove(item["id"])
                        if item["modification_time"] > self.last_sync_time:
                            cnt["update"] += 1
                            self.index_record(item)
                        else:
                            cnt["remain"] += 1
                    else:
                        cnt["add"] += 1
                        self.index_record(item)
                cnt["delete"] = len(ids_es)
                for doc_id in ids_es:
                    self.es.es.delete(index=self.es.index, id=doc_id)
                self.es.es.indices.refresh(index=self.index)
                self.last_sync_time = now
                logging.info("add: %d, update: %d, remain %d, delete: %d" % (cnt["add"], cnt["update"], cnt["remain"], cnt["delete"]))

    def index_record(self, record):
        questions = list()
        questions.append(
            {"question": record["standard_question"], "is_standard": True, "id": record["id"]})
        for question in json.loads(record["similar_questions"]):
            questions.append(
                {"question": question, "is_standard": False, "id": record["id"]})
        doc = {
            "id": record["id"],
            "standard_question": record["standard_question"],
            "questions": questions,
            "related_questions": json.loads(record["related_questions"]),
            "answers": json.loads(record["answers"]),
            "is_published": bool(record["is_published"])
        }
        self.es.es.index(index=self.index, body=doc, id=record["id"])

if __name__ == "__main__":
    # config logger
    config_logger('logs/qa_synchronize')

    # default config
    default_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yml')
    if os.path.exists(default_config_file):
        with open(default_config_file, 'r', encoding='utf-8') as f:
            conf = yaml.safe_load(f)
    # custom config
    custom_conf = {}
    custom_config_file = 'config.yml'
    if os.path.exists(custom_config_file):
        with open(custom_config_file, 'r', encoding='utf-8') as f:
            custom_conf = yaml.safe_load(f)
    merge_config(conf, custom_conf)  # merge custom_conf to default_conf
    conf_kb = conf["bot"]["kb"]

    synchonizer = Synchonizer(conf_kb)

    logging.info("KBQA switch: %s" % conf_kb["switch"])
    if conf_kb["switch"]:
        tornado.ioloop.PeriodicCallback(synchonizer.sync_from_mysql, conf_kb["sync_period"] * 1000).start()  # start scheduler 每隔2s执行一次f2s
        logging.info('qa synchonizer started.')
        tornado.ioloop.IOLoop.current().start()




