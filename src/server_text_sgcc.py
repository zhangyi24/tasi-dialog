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

RESPONSE_BODY_HANGUP = {
    "callId": "",
    "messageId": "",
    "actionType": "0",
    "actionContent": ""
}

RESPONSE_BODY_FWD = {
    "callId": "",
    "messageId": "",
    "actionType": "1",
    "actionContent": "dldf"
}

RESPONSE_BODY_INTERACT = {
    "callId": "",
    "messageId": "",
    "actionType": "2",
    "actionContent": "",
    "answerType": "1",
    "answerContent": ""
}

INPUT_CHANNEL_CODE = {
    "asr": "10",
    "keyboard": "01"
}


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, bot, conf):
        self.bot = bot
        self.conf = conf

    def prepare(self):
        logging.info('req_headers: %s' % dict(self.request.headers))
        self.req_body = json.loads(self.request.body) if self.request.body else {}
        logging.info('req_body: %s' % self.req_body)
        self.set_header(name='Content-Type', value='application/json; charset=UTF-8')

    def get(self):
        self.write('tasi-dialog-server-text-sgcc')

    def post(self):
        resp_body = None
        assert self.req_body['firstSign'] in ["1", "2"]
        if self.req_body['firstSign'] == "1":
            call_info = {
                "modeType": self.req_body.get("modeType", ""),
                "mediaType": self.req_body.get("mediaType", ""),
                "reqSource": self.req_body.get("reqSource", ""),
                "beginTime": self.req_body.get("beginTime", ""),
                "messageProvider": self.req_body.get("messageProvider", ""),
                "channelCode": self.req_body.get("channelCode", ""),
                "callerNo": self.req_body.get("callerNo", ""),
                "callerNoType": self.req_body.get("callerNoType", "")
            }
            self.bot.init(user_id=self.req_body['callId'], user_info=[],
                          call_info=call_info)
            call = self.bot.users[self.req_body['callId']]
            call['resp_queue'] = collections.deque()

            # 获取开场白
            bot_resp, call['call_status'] = self.bot.greeting(user_id=self.req_body['callId'])
            # 正常交互
            if call['call_status'] == 'on':
                resp_body = self.generate_resp_body_interact(bot_resp)
            # 机器人发起挂断或转人工
            elif call['call_status'] == 'hangup':
                resp_body = self.generate_resp_body_interact(bot_resp, input=False)
                call['resp_queue'].append(self.generate_resp_body_hangup())
            elif call['call_status'] == 'fwd':
                resp_body = self.generate_resp_body_interact(bot_resp, input=False)
                call['resp_queue'].append(self.generate_resp_body_fwd())
        else:
            if self.req_body['callId'] not in self.bot.users:
                error_info = f"there is no call whose callId is {self.req_body['callId']}."
                self.throw_error(400, error_info)
            # 根据callId获取会话信息
            call = self.bot.users[self.req_body['callId']]
            # 用户主动挂断
            if self.req_body['messageType'] == "03":
                call['resp_queue'].clear()
                resp_body = self.generate_resp_body_hangup()
            # 有待完成指令
            elif call['resp_queue']:
                resp_body = call['resp_queue'].popleft()
            else:
                input = ''
                if self.req_body['messageType'] in ['01', '02']:
                    input = self.req_body['messageContent']
                bot_resp, call['call_status'] = self.bot.response(self.req_body['callId'], input)
                # 正常交互
                if call['call_status'] == 'on':
                    resp_body = self.generate_resp_body_interact(bot_resp)
                # 机器人发起挂断或转人工
                elif call['call_status'] == 'hangup':
                    resp_body = self.generate_resp_body_interact(bot_resp, input=False)
                    call['resp_queue'].append(self.generate_resp_body_hangup())
                elif call['call_status'] == 'fwd':
                    resp_body = self.generate_resp_body_interact(bot_resp, input=False)
                    call['resp_queue'].append(self.generate_resp_body_fwd())
        self.write_resp(resp_body)
        self.bot.users[resp_body['callId']]['last_resp_body'] = resp_body
        if resp_body['actionType'] != "2":
            del self.bot.users[resp_body['callId']]

    def generate_resp_body_interact(self, bot_resp, input=True):
        resp_body = copy.deepcopy(RESPONSE_BODY_INTERACT)
        if not self.conf["keyboard_access"]:
            bot_resp["input_channel"] = INPUT_CHANNEL_CODE["asr"]
        resp_body.update({
            "callId": self.req_body['callId'],
            "messageId": self.req_body['messageId'],
            "actionContent": f'1{bot_resp["input_channel"]}' if input else '100',
            "answerContent": bot_resp['content']
        })
        return resp_body

    def generate_resp_body_hangup(self):
        resp_body = copy.deepcopy(RESPONSE_BODY_HANGUP)
        resp_body.update({
            "callId": self.req_body['callId'],
            "messageId": self.req_body['messageId']
        })
        return resp_body

    def generate_resp_body_fwd(self):
        resp_body = copy.deepcopy(RESPONSE_BODY_FWD)
        resp_body.update({
            "callId": self.req_body['callId'],
            "messageId": self.req_body['messageId']
        })
        return resp_body

    def throw_error(self, status_code, reason):
        logging.info(reason)
        self.set_status(status_code, reason=reason)
        raise tornado.web.Finish()

    def write_resp(self, resp_body):
        self.write(json.dumps(resp_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
        logging.info('[dialog] resp_headers: %s' % dict(self._headers))
        logging.info('[dialog] resp_body: %s' % resp_body)


if __name__ == "__main__":
    # config logger
    config_logger('logs/text-sgcc')

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
    conf_text = conf["text-sgcc"]

    # bot
    logging.info('loading bot...')
    bot = Bot(bot_config=conf["bot"])
    logging.info('bot loaded.')
    # app
    application = tornado.web.Application([
        (r"/", MainHandler, dict(bot=bot, conf=conf_text)),
    ])
    application.listen(conf_text['port'])
    logging.info('listening on 127.0.0.1:%s...' % conf_text['port'])
    tornado.ioloop.IOLoop.current().start()
