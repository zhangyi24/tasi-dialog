# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Dialog server (text version)."""

# coding=utf-8
import json
import argparse
import datetime
import logging
import logging.config
import copy
import collections
import os

import yaml
import tornado.ioloop
import tornado.httpclient
import tornado.escape
import tornado.web

from agent import Bot
from utils.logger import config_logger
from utils.config import merge_config


class KbHandler(tornado.web.RequestHandler):
    def initialize(self, es=None):
        self.es = es

    def prepare(self):
        logging.info('req_headers: %s' % dict(self.request.headers))
        self.req_body = json.loads(self.request.body) if self.request.body else {}
        logging.info('req_body: %s' % self.req_body)
        self.set_header(name='Content-Type', value='application/json; charset=UTF-8')

    def get(self):
        self.write('SPMIBOT')

    def post(self):
        resp_body = None
        if "action" not in self.req_body:
            self.set_status(400, reason="The specified parameter 'action' is missing.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "query_categories":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "describe_category":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "create_category":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "update_category":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "delete_category":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "query_core_words":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "describe_core_word":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "create_core_word":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "update_core_word":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "delete_core_word":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "add_synonym":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "remove_synonym":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()

        elif self.req_body["action"] == "query_knowledges":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "describe_knowledge":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "create_knowledge":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "update_knowledge":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "delete_knowledge":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "publish_knowledge":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "disable_knowledge":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        elif self.req_body["action"] == "move_knowledge_category":
            self.set_status(500, reason="Interface not implemented yet.")
            raise tornado.web.Finish()
        else:
            self.set_status(400, reason="Invalid action: %s" % self.req_body["action"])
            raise tornado.web.Finish()
        if resp_body is not None:
            self.write(self.json_encode(resp_body))
            logging.info('resp_headers: %s' % dict(self._headers))
            logging.info('resp_body: %s' % resp_body)

    def json_encode(self, obj):
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


if __name__ == "__main__":
    # config logger
    config_logger('logs/admin')

    # default config
    default_config_file = os.path.join(os.path.dirname(__file__), 'config', 'config.yml')
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
    conf_admin = conf["admin"]

    # es
    
    # app
    application = tornado.web.Application([
        (r"/kb", KbHandler),
    ])
    application.listen(conf_admin['port'])
    logging.info('listening on 127.0.0.1:%s...' % conf_admin['port'])
    tornado.ioloop.IOLoop.current().start()
