# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""crs server."""

# coding=utf-8
import json
import argparse
import datetime
import logging
import logging.config
import copy
import collections
import threading
import time
import os

import yaml
import tornado.ioloop
import tornado.web
import requests

from agent import Bot
from utils.postgresql import PostgreSQLWrapper
from utils.logger import config_logger
from utils.str_process import replace_space
from utils.config import merge_config

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, conf_crs, users):
        self.conf_crs = conf_crs
        self.users = users

    async def prepare(self):
        logging.info('[crs] req_headers: %s' % dict(self.request.headers))
        self.req_body = json.loads(self.request.body) if self.request.body else {}
        logging.info('[crs] req_body: %s' % self.req_body)
        self.set_header(name='Content-Type', value='application/json; charset=UTF-8')

    async def get(self):
        self.write('SPMIBOT')

    async def post(self):
        resp_body = None
        assert self.req_body['inaction'] in [8, 9, 11, 0]
        if self.req_body['inaction'] == 8:
            # todo:获取场景id
            scene_id = self.req_body['inparams']['extend'].split('#')[0]
            if scene_id not in self.conf_crs["route"]:
                self.throw_error(400, f"[crs] There is no bot that corresponds to 'scene_id': {scene_id}.")
            bot_url = self.conf_crs["route"][scene_id]
            self.users.update({self.req_body['userid']: {"bot_url": bot_url}})
            # 尝试获取resp
            resp_body = self.post_to_bot(url=bot_url, req_body=self.req_body)
            self.write_resp(resp_body)
        else:
            if self.req_body['userid'] not in self.users:
                self.throw_error(400, f"[crs] There is no user whose user_id is {self.req_body['userid']}.")
            # 根据user_id获取用户信息
            user = self.users[self.req_body['userid']]
            bot_url = user["bot_url"]
            # 尝试获取resp
            resp_body = self.post_to_bot(url=bot_url, req_body=self.req_body)
            self.write_resp(resp_body)
        if resp_body['outaction'] == '10':
            self.users.clear()

    def throw_error(self, status_code, reason):
        logging.info(reason)
        self.set_status(status_code, reason=reason)
        raise tornado.web.Finish()

    def write_resp(self, resp_body):
        self.write(json.dumps(resp_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
        logging.info('[crs] resp_headers: %s' % dict(self._headers))
        logging.info('[crs] resp_body: %s' % resp_body)

    def post_to_bot(self, url, req_body):
        try:
            resp = requests.post(url=url, json=req_body)
            if resp.status_code != 200:
                self.throw_error(resp.status_code, resp.reason)
            resp_body = resp.json() if resp.content else {}
            return resp_body
        except requests.exceptions.ConnectionError as e:
            self.throw_error(500, f"Can not connect to the specified robot.")

if __name__ == "__main__":
    # config logger
    config_logger('logs/crs')

    # builtin_conf
    builtin_config_file = os.path.join(os.path.dirname(__file__), 'config', 'config.yml')
    if os.path.exists(builtin_config_file):
        with open(builtin_config_file, 'r', encoding='utf-8') as f:
            conf = yaml.safe_load(f)

    # custom config
    custom_conf = {}
    custom_config_file_path = "config.yml"
    if os.path.exists(custom_config_file_path):
        with open(custom_config_file_path, 'r', encoding='utf-8') as f:
            custom_conf = yaml.safe_load(f)
    merge_config(conf, custom_conf)
    conf_crs = conf["crs"]

    # app
    application = tornado.web.Application([
        (r"/", MainHandler, dict(conf_crs=conf_crs, users={})),
    ])
    application.listen(conf_crs['port'])
    logging.info('listening on 127.0.0.1:%s...' % conf_crs['port'])
    tornado.ioloop.IOLoop.current().start()
