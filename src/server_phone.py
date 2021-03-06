# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Dialog server (phone version)."""

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

RESPONSE_BODY_4 = {
    "ret": 0,
    "userid": "",
    "outaction": '4',
    "outparams": {
        "call_id": "",
        "call_sor_id": "",
        "call_dst_id": "",
        "entrance_id": ""
    }
}

RESPONSE_BODY_9 = {
    "ret": 0,
    "userid": "",
    "outaction": '9',
    "outparams": {
        "call_id": "",
        "inter_idx": "",
        "model_type": "",
        "prompt_type": "",
        "prompt_wav": "",
        "prompt_text": "",
        "prompt_src": "",
        "timeout": "",
        "org": "",
        "grammar": "",
        "newsess": "",
        "res_node_lst": "",
        "res_parse_mode": "",
        "extended_field": ""
    }
}

RESPONSE_BODY_10 = {
    "ret": 0,
    "userid": "",
    "outaction": '10',
    "outparams": {
        "call_id": "",
        "call_sor_id": "",
        "call_dst_id": "",
        "start_time": "",
        "end_time": "",
        "region_id": "",
        "entrance_id": "",
        "exit_id": "",
        "user_type_id": "",
        "suilu_region_id": ""
    }
}

RESPONSE_BODY_11 = {
    "ret": 0,
    "userid": "",
    "outaction": '11',
    "outparams": {
        "call_id": "",
        "inter_idx": "",
        "call_sor_id": "",
        "trans_type": "",
        "route_value": "",
        "queue_id": ""
    }
}

RESPONSE_BODY_0 = {
    "ret": 0,
    "userid": "",
    "outaction": "0",
    "outparams": {
        "call_id": "",
        "call_sor_id": "",
        "call_dst_id": "",
        "att_status": "",
        "queue_id": ""
    }
}


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, bot, db, bot_conf, asr_conf):
        self.bot = bot
        self.db = db
        self.bot_conf = bot_conf
        self.asr_conf = asr_conf

    async def prepare(self):
        logging.info('[dialog] req_headers: %s' % dict(self.request.headers))
        self.req_body = json.loads(self.request.body) if self.request.body else {}
        logging.info('[dialog] req_body: %s' % self.req_body)
        self.set_header(name='Content-Type', value='application/json; charset=UTF-8')

    async def get(self):
        self.write('SPMIBOT')

    async def post(self):
        resp_body = None
        assert self.req_body['inaction'] in [8, 9, 11, 0]
        if self.req_body['inaction'] == 8:
            # 处理扩展字段
            user_info = self.req_body['inparams']['extend'].split('#')[1:]
            # 处理通话参数
            call_info = copy.deepcopy(self.req_body['inparams'])
            if not self.bot_conf["fwd"]["queue_id_updatable"]:
                call_info["queue_id"] = self.bot_conf["fwd"]["queue_id"]
            # 初始化一个机器人，返回开场白
            self.bot.init(call_id=self.req_body['userid'], user_info=user_info,
                          call_info=call_info,
                          task_id=self.req_body['inparams']['strategy_params'].split('#')[0])
            call = self.bot.calls[self.req_body['userid']]
            call['inter_idx'] = '1'
            call['resp_queue'] = collections.deque()

            # 为了将对话信息入库，首先需要将用户基本信息入库
            if self.db:
                self.db.add_user(call['call_info'].get('call_sor_id', ''))
            # 获取开场白
            bot_resp, call['call_status'] = self.bot.greeting(call_id=self.req_body['userid'])
            bot_resp['content'] = replace_space(bot_resp['content'])
            resp_body = self.generate_resp_body(call, bot_resp)

        elif self.req_body['inaction'] == 9:
            if self.req_body['userid'] not in self.bot.calls:
                error_info = '[dialog] there is no call whose userid is \'%s\'.' % self.req_body['userid']
                logging.info(error_info)
                self.set_status(400, reason=error_info)
                raise tornado.web.Finish()
            # 根据userid获取呼叫信息
            call = self.bot.calls[self.req_body['userid']]
            # 用户主动挂断
            if self.req_body['inparams']['flow_result_type'] == '3' and self.req_body['inparams']['input'] == 'hangup':
                call['resp_queue'].clear()
                resp_body = self.generate_resp_body_hangup(call)
            # 上次指令执行超时，重发
            elif self.req_body['inparams']['flow_result_type'] == '3' and self.req_body['inparams'][
                'input'] == 'timeout':
                resp_body = self.bot.calls[self.req_body['userid']]['last_resp_body']
            # 有待完成指令
            elif call['resp_queue']:
                resp_body = call['resp_queue'].popleft()
            else:
                call['inter_idx'] = str(int(self.req_body['inparams']['inter_idx']) + 1)
                user_input, asr_record_path = '', ''
                if self.req_body['inparams']['flow_result_type'] in ['1', '2']:
                    user_input, asr_record_path = self.parse_asr_result(self.req_body['inparams']['input'])
                if user_input:
                    call['history'].append('用户：' + user_input)
                    if self.db:
                        self.db.add_msg(user=call['call_info'].get('call_sor_id', ''),
                                        receipt='bot', msg=user_input, task_id=call['task_id'],
                                        asr_record_path=asr_record_path)
                bot_resp, call['call_status'] = self.bot.response(self.req_body['userid'], user_input)
                bot_resp['content'] = replace_space(bot_resp['content'])
                resp_body = self.generate_resp_body(call, bot_resp)

        # 判断呼叫转移是否成功
        elif self.req_body['inaction'] == 11:
            call = self.bot.calls[self.req_body['userid']]
            trans_success = self.req_body['inparams']['trans_result'] == '1'
            resp_body = self.generate_resp_body_hangup(call)  # 无论是否转移成功，这通电话已经结束。

        # 判断呼叫转移队列是否锁定成功
        elif self.req_body['inaction'] == 0:
            call = self.bot.calls[self.req_body['userid']]
            queue_locked = self.req_body['inparams']['att_status'] == '1'
            if queue_locked:
                resp_body = self.generate_resp_body_fwd(call)
            else:
                resp_body = self.generate_resp_body_hangup(call)

        self.write(json.dumps(resp_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
        call = self.bot.calls[resp_body['userid']]
        bot_say_something = resp_body['outaction'] == '9' and resp_body['outparams']['model_type'].startswith('1') and \
                            resp_body['outparams']['prompt_type'] == '2'
        retransmission = self.req_body['inaction'] == 9 and self.req_body['inparams']['flow_result_type'] == '3' and \
                         self.req_body['inparams'][
                             'input'] == 'timeout'
        if bot_say_something and not retransmission:
            call['history'].append('机器人：' + resp_body['outparams']['prompt_text'])
            if self.db:
                self.db.add_msg(user='bot',
                                receipt=call['call_info'].get('call_sor_id', ''), msg=resp_body['outparams']['prompt_text'],
                                task_id=call['task_id'])
        call['last_resp_body'] = resp_body
        logging.info('[dialog] resp_headers: %s' % dict(self._headers))
        logging.info('[dialog] resp_body: %s' % resp_body)
        if self.db:
            threading.Thread(target=self.db.write_msgs, name='SQL').start()
        if resp_body['outaction'] in ['4', '10']:
            del self.bot.calls[resp_body['userid']]
            threading.Thread(target=self.save_results, args=(call,), name='call_post_process').start()

    def save_results(self, call):
        save_result_conf = self.bot_conf["save_result"]
        if save_result_conf['switch'] is True:
            req_body = {
                "callid": "",
                "entranceId": "",
                "eventId": "",
                "listId": "",
                "custId": "",
                "content": "",
                "robotAction": "",
                "callResult": "",
                "comcode": "",
                "isToacd": ""
            }
            self.bot.convert_results_to_codes(call)
            req_body.update({
                "callid": call["call_info"].get('call_id', ''),
                "entranceId": call["call_info"].get('entranceId', ''),
                "content": '#'.join(call['history']),
                "isToacd": '0' if call['call_status'] == 'fwd' else '1',
                "callResult": '#'.join(call['results'])
            })
            req_body.update(dict(zip(("eventId", "custId", "listId"), call['call_info']['strategy_params'].split('#'))))
            extend = call['call_info'].get('extend', '').split('#')
            for i in range(len(extend)):
                req_body.update({'col%d' % (i + 1): extend[i]})
            req_body = [req_body]
            resp = requests.post(save_result_conf["url"],
                                 data=json.dumps(req_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
            logging.info('[save_result] req_headers: %s' % resp.request.headers)
            logging.info('[save_result] req_body: %s' % resp.request.body.decode('utf-8'))
            logging.info('[save_result] resp_headers: %s' % resp.headers)
            logging.info('[save_result] resp_body: %s' % resp.json())

    def parse_asr_result(self, input_raw):
        user_input, asr_record_path = '', ''
        if '[' not in input_raw or ']' not in input_raw:
            return input_raw, ''
        asr_record_path, user_input = input_raw.rstrip(']').rsplit('[', 1)
        if asr_record_path and 'record_dir' in self.asr_conf:
            asr_record_path = os.path.join(self.asr_conf['record_dir'], asr_record_path)
        return user_input, asr_record_path

    def makeup_model_type(self, speak_switch, input_channels=None):
        model_type = ""
        model_type += "1" if speak_switch else "0"
        if not input_channels:
            model_type += "000000"
        else:
            model_type += "1" if input_channels["asr"]["switch"] else "0"
            model_type += "1" if input_channels["keyboard"]["switch"] else "0"
            model_type += "%02d" % input_channels["keyboard"]["max_length"]
            model_type += "01"
        return model_type

    def generate_resp_body(self, call, bot_resp):
        # 正常交互
        if call['call_status'] == 'on':
            if bot_resp['allow_interrupt']:
                resp_body = self.generate_resp_body_speak_listen(call, bot_resp)
            else:
                resp_body = self.generate_resp_body_speak(call, bot_resp)
                call['resp_queue'].append(self.generate_resp_body_listen(call, bot_resp))

        # 机器人发起挂断
        elif call['call_status'] == 'hangup':
            resp_body = self.generate_resp_body_speak(call, bot_resp)
            call['resp_queue'].append(self.generate_resp_body_hangup(call))

        # 机器人发起呼叫转移
        elif call['call_status'] == 'fwd':
            if self.bot_conf["fwd"]["lock_before_fwd"]:
                resp_body = self.generate_resp_body_speak(call, bot_resp)
                call['resp_queue'].append(self.generate_resp_body_lock_queue(call))
            else:
                resp_body = self.generate_resp_body_speak(call, bot_resp)
                call['resp_queue'].append(self.generate_resp_body_fwd(call))

        elif call['call_status'] == 'ivr':
            resp_body = self.generate_resp_body_speak(call, bot_resp)
            call['resp_queue'].append(self.generate_resp_body_ivr(call))

        else:
            logging.error(f"invalid call_status: {call['call_status']}")
        return resp_body

    def generate_resp_body_speak(self, call, bot_resp):
        resp_body = copy.deepcopy(RESPONSE_BODY_9)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": call["call_info"].get('call_id', ''),
            "inter_idx": call['inter_idx'],
            "model_type": self.makeup_model_type(speak_switch=True, input_channels=None),
            "prompt_type": '2',
            "prompt_wav": '',
            "prompt_text": bot_resp["content"],
            "prompt_src": bot_resp['src'],
            "timeout": '0'
        })
        return resp_body

    def generate_resp_body_listen(self, call, bot_resp, timeout='5'):
        resp_body = copy.deepcopy(RESPONSE_BODY_9)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": call["call_info"].get('call_id', ''),
            "inter_idx": call['inter_idx'],
            "model_type": self.makeup_model_type(speak_switch=False, input_channels=bot_resp["input_channels"]),
            "prompt_type": '1',
            "timeout": timeout
        })
        return resp_body

    def generate_resp_body_speak_listen(self, call, bot_resp, timeout='5'):
        resp_body = copy.deepcopy(RESPONSE_BODY_9)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": call["call_info"].get('call_id', ''),
            "inter_idx": call['inter_idx'],
            "model_type": self.makeup_model_type(speak_switch=True, input_channels=bot_resp["input_channels"]),
            "prompt_type": '2',
            "prompt_wav": '',
            "prompt_text": bot_resp["content"],
            "prompt_src": bot_resp['src'],
            "timeout": timeout
        })

        return resp_body

    def generate_resp_body_hangup(self, call):
        resp_body = copy.deepcopy(RESPONSE_BODY_10)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": call['call_info'].get('call_id', ''),
            "call_sor_id": call['call_info'].get('call_sor_id', ''),
            "call_dst_id": call['call_info'].get('call_dst_id', ''),
            "start_time": call['call_info'].get('start_time', ''),
            "end_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3],
            "entrance_id": call['call_info'].get('entrance_id', '')
        })
        return resp_body

    def generate_resp_body_fwd(self, call, dest=None):
        resp_body = copy.deepcopy(RESPONSE_BODY_11)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": call['call_info'].get('call_id', ''),
            "inter_idx": call["inter_idx"],
            "call_sor_id": call['call_info'].get('call_sor_id', ''),
            "queue_id": call['call_info'].get('queue_id', '')
        })
        if dest is None:
            resp_body["outparams"].update({
                "trans_type": "1",
                "queue_id": call['call_info'].get('queue_id', '')
            })
        else:
            resp_body["outparams"].update({
                "trans_type": "2",
                "queue_id": dest
            })

        return resp_body

    def generate_resp_body_lock_queue(self, call):
        resp_body = copy.deepcopy(RESPONSE_BODY_0)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": call['call_info'].get('call_id', ''),
            "call_sor_id": call['call_info'].get('call_sor_id', ''),
            "call_dst_id": call['call_info'].get('call_dst_id', ''),
            "att_status": 'true',
            "queue_id": call['call_info'].get('queue_id', '')
        })
        return resp_body

    def generate_resp_body_ivr(self, call):
        resp_body = copy.deepcopy(RESPONSE_BODY_4)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": call['call_info'].get('call_id', ''),
            "call_sor_id": call['call_info'].get('call_sor_id', ''),
            "call_dst_id": call['call_info'].get('call_dst_id', ''),
            "entrance_id": call['call_info'].get('entrance_id', '')
        })
        return resp_body


if __name__ == "__main__":
    # config logger
    config_logger('logs/phone')

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
    conf_phone = conf["phone"]

    # config db
    db = None
    if 'postgresql' not in conf_phone:
        logging.warning('postgresql database config is not available.')
        db = None
    elif not conf_phone['postgresql'].get('switch', False):
        logging.warning("postgresql database config 'switch': False.")
        db = None
    else:
        for _ in range(5):
            try:
                db = PostgreSQLWrapper(conf_phone['postgresql'])
                logging.info('connect to the postgresql database successfully.')
                break
            except:
                logging.warning('fail to connect to the postgresql database.')
                time.sleep(0.5)

    # load bot
    logging.info('loading bot...')
    bot = Bot(interruptable=conf_phone['bot']['interruptable'], bot_config=conf["bot"])
    logging.info('bot loaded.')

    # app
    application = tornado.web.Application([
        (r"/", MainHandler, dict(bot=bot, db=db, bot_conf=conf_phone['bot'], asr_conf=conf_phone['asr'])),
    ])
    application.listen(conf_phone['port'])
    logging.info('listening on 127.0.0.1:%s...' % conf_phone['port'])
    tornado.ioloop.IOLoop.current().start()
