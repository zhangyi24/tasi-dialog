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
from utils.mysql import MySQLWrapper
from utils.postgresql import PostgreSQLWrapper
from utils.logger import config_logger

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
            # 初始化一个机器人，返回开场白
            self.bot.init(user_id=self.req_body['userid'], user_info=user_info,
                          call_info=self.req_body['inparams'],
                          task_id=self.req_body['inparams']['strategy_params'].split('#')[0])
            user = self.bot.users[self.req_body['userid']]
            user['inter_idx'] = '1'
            user['resp_queue'] = collections.deque()

            # 为了将对话信息入库，首先需要将用户基本信息入库
            if self.db:
                self.db.add_user(user['call_info'].get('call_sor_id', ''))
            # 获取开场白
            bot_resp, user['call_status'] = self.bot.greeting(user_id=self.req_body['userid'])
            # 正常交互
            if user['call_status'] == 'on':
                if bot_resp['allow_interrupt']:
                    resp_body = self.generate_resp_body_speak_listen(user, bot_resp['content'])
                else:
                    resp_body = self.generate_resp_body_speak(user, bot_resp['content'])
                    user['resp_queue'].append(self.generate_resp_body_listen(user))

            # 机器人发起挂断
            elif user['call_status'] == 'hangup':
                resp_body = self.generate_resp_body_speak(user, bot_resp['content'])
                user['resp_queue'].append(self.generate_resp_body_hangup(user))

            # 机器人发起呼叫转移
            elif user['call_status'] == 'fwd':
                if self.bot_conf["lock_before_fwd"]:
                    resp_body = self.generate_resp_body_lock_queue(user)
                    user['resp_queue'].append(
                        self.generate_resp_body_speak(user, bot_resp['content']))
                else:
                    resp_body = self.generate_resp_body_speak(user, '正在为您转接至人工')
                    user['resp_queue'].append(self.generate_resp_body_fwd(user))

        elif self.req_body['inaction'] == 9:
            if self.req_body['userid'] not in self.bot.users:
                logging.info('[dialog] there is no user whose user_id is \'%s\'.' % self.req_body['userid'])
                return
            # 根据user_id获取用户信息
            user = self.bot.users[self.req_body['userid']]
            # 用户主动挂断
            if self.req_body['inparams']['flow_result_type'] == '3' and self.req_body['inparams']['input'] == 'hangup':
                user['resp_queue'].clear()
                resp_body = self.generate_resp_body_hangup(user)
            # 上次指令执行超时，重发
            elif self.req_body['inparams']['flow_result_type'] == '3' and self.req_body['inparams'][
                'input'] == 'timeout':
                resp_body = self.bot.users[self.req_body['userid']]['last_resp_body']
            # 有待完成指令
            elif user['resp_queue']:
                resp_body = user['resp_queue'].popleft()
            else:
                user['inter_idx'] = str(int(self.req_body['inparams']['inter_idx']) + 1)
                user_input, asr_record_path = '', ''
                if self.req_body['inparams']['flow_result_type'] in ['1', '2']:
                    user_input, asr_record_path = self.parse_asr_result(self.req_body['inparams']['input'])
                if user_input:
                    if self.db:
                        self.db.add_msg(user=user['call_info'].get('call_sor_id', ''),
                                        receipt='bot', msg=user_input, task_id=user['task_id'],
                                        asr_record_path=asr_record_path)
                    user['history'].append('用户：' + user_input)
                bot_resp, user['call_status'] = self.bot.response(self.req_body['userid'], user_input)

                # 正常交互
                if user['call_status'] == 'on':
                    if bot_resp['allow_interrupt']:
                        resp_body = self.generate_resp_body_speak_listen(user, bot_resp['content'])
                    else:
                        resp_body = self.generate_resp_body_speak(user, bot_resp['content'])
                        user['resp_queue'].append(self.generate_resp_body_listen(user))

                # 机器人发起挂断
                elif user['call_status'] == 'hangup':
                    resp_body = self.generate_resp_body_speak(user, bot_resp['content'])
                    user['resp_queue'].append(self.generate_resp_body_hangup(user))

                # 机器人发起呼叫转移
                elif user['call_status'] == 'fwd':
                    if self.bot_conf["lock_before_fwd"]:
                        resp_body = self.generate_resp_body_lock_queue(user)
                        user['resp_queue'].append(
                            self.generate_resp_body_speak(user, bot_resp['content']))
                    else:
                        resp_body = self.generate_resp_body_speak(user, '正在为您转接至人工')
                        user['resp_queue'].append(self.generate_resp_body_fwd(user))

        # 判断呼叫转移是否成功
        elif self.req_body['inaction'] == 11:
            user = self.bot.users[self.req_body['userid']]
            trans_success = self.req_body['inparams']['trans_result'] == '1'
            resp_body = self.generate_resp_body_hangup(user)  # 无论是否转移成功，这通电话已经结束。

        # 判断呼叫转移队列是否锁定成功
        elif self.req_body['inaction'] == 0:
            user = self.bot.users[self.req_body['userid']]
            queue_locked = self.req_body['inparams']['att_status'] == '1'
            if queue_locked:
                user['resp_queue'].popleft()
                resp_body = self.generate_resp_body_speak(user, '正在为您转接至人工')
                user['resp_queue'].append(self.generate_resp_body_fwd(user))
            else:
                resp_body = user['resp_queue'].popleft()
                user['resp_queue'].append(self.generate_resp_body_hangup(user))

        self.write(json.dumps(resp_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
        user = self.bot.users[resp_body['userid']]
        bot_say_something = resp_body['outaction'] == '9' and resp_body['outparams']['model_type'].startswith('1') and \
                            resp_body['outparams']['prompt_type'] == '2'
        retransmission = self.req_body['inaction'] == 9 and self.req_body['inparams']['flow_result_type'] == '3' and \
                         self.req_body['inparams'][
                             'input'] == 'timeout'
        if bot_say_something and not retransmission:
            user['history'].append('机器人：' + resp_body['outparams']['prompt_text'])
            if self.db:
                self.db.add_msg(user='bot',
                                receipt=user['call_info'].get('call_sor_id', ''), msg=resp_body['outparams']['prompt_text'],
                                task_id=user['task_id'])
        user['last_resp_body'] = resp_body
        logging.info('[dialog] resp_headers: %s' % dict(self._headers))
        logging.info('[dialog] resp_body: %s' % resp_body)
        if self.db:
            threading.Thread(target=self.db.write_msgs, name='SQL').start()
        if resp_body['outaction'] == '10':
            del self.bot.users[resp_body['userid']]
            threading.Thread(target=self.save_results, args=(user,), name='call_post_process').start()

    def save_results(self, user):
        if 'result_save_url' in self.bot_conf:
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
            self.bot.convert_results_to_codes(user)
            req_body.update({
                "callid": user["call_info"].get('call_id', ''),
                "entranceId": user["call_info"].get('entranceId', ''),
                "content": '#'.join(user['history']),
                "isToacd": '0' if user['call_status'] == 'fwd' else '1',
                "callResult": '#'.join(user['results'])
            })
            req_body.update(dict(zip(("eventId", "custId", "listId"), user['call_info']['strategy_params'].split('#'))))
            extend = user['call_info'].get('extend', '').split('#')
            for i in range(len(extend)):
                req_body.update({'col%d' % (i + 1): extend[i]})
            req_body = [req_body]
            resp = requests.post(self.bot_conf['result_save_url'],
                                 data=json.dumps(req_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
            logging.info('[save_result] req_headers: %s' % resp.request.headers)
            logging.info('[save_result] req_body: %s' % resp.request.body.decode('utf-8'))
            logging.info('[save_result] resp_headers: %s' % resp.headers)
            logging.info('[save_result] resp_body: %s' % resp.json())

    def parse_asr_result(self, input_raw):
        user_input, asr_record_path = '', ''
        if '[' not in input_raw:
            return user_input, asr_record_path
        asr_record_path, user_input = input_raw.rstrip(']').rsplit('[', 1)
        if asr_record_path and 'record_dir' in self.asr_conf:
            asr_record_path = os.path.join(self.asr_conf['record_dir'], asr_record_path)
        return user_input, asr_record_path

    def generate_resp_body_speak(self, user, prompt):
        resp_body = copy.deepcopy(RESPONSE_BODY_9)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": user["call_info"].get('call_id', ''),
            "inter_idx": user['inter_idx'],
            "model_type": "1000000",
            "prompt_type": '2',
            "prompt_wav": '',
            "prompt_text": prompt,
            "timeout": '0'
        })
        return resp_body

    def generate_resp_body_listen(self, user, model_type='0100000', timeout='5'):
        resp_body = copy.deepcopy(RESPONSE_BODY_9)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": user["call_info"].get('call_id', ''),
            "inter_idx": user['inter_idx'],
            "model_type": model_type,
            "prompt_type": '1',
            "timeout": timeout
        })
        return resp_body

    def generate_resp_body_speak_listen(self, user, prompt, model_type='1100000', timeout='5'):
        resp_body = copy.deepcopy(RESPONSE_BODY_9)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": user["call_info"].get('call_id', ''),
            "inter_idx": user['inter_idx'],
            "model_type": model_type,
            "prompt_type": '2',
            "prompt_wav": '',
            "prompt_text": prompt,
            "timeout": timeout
        })

        return resp_body

    def generate_resp_body_hangup(self, user):
        resp_body = copy.deepcopy(RESPONSE_BODY_10)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": user['call_info'].get('call_id', ''),
            "call_sor_id": user['call_info'].get('call_sor_id', ''),
            "call_dst_id": user['call_info'].get('call_dst_id', ''),
            "start_time": user['call_info'].get('start_time', ''),
            "end_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3],
            "entrance_id": user['call_info'].get('entrance_id', '')
        })
        return resp_body

    def generate_resp_body_fwd(self, user, dest=None):
        resp_body = copy.deepcopy(RESPONSE_BODY_11)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": user['call_info'].get('call_id', ''),
            "inter_idx": user["inter_idx"],
            "call_sor_id": user['call_info'].get('call_sor_id', ''),
            "queue_id": user['call_info'].get('queue_id', '')
        })
        if dest is None:
            resp_body["outparams"].update({
                "trans_type": "1",
                "queue_id": user['call_info'].get('queue_id', '')
            })
        else:
            resp_body["outparams"].update({
                "trans_type": "2",
                "queue_id": dest
            })

        return resp_body

    def generate_resp_body_lock_queue(self, user):
        resp_body = copy.deepcopy(RESPONSE_BODY_0)
        resp_body.update({"userid": self.req_body['userid']})
        resp_body["outparams"].update({
            "call_id": user['call_info'].get('call_id', ''),
            "call_sor_id": user['call_info'].get('call_sor_id', ''),
            "call_dst_id": user['call_info'].get('call_dst_id', ''),
            "att_status": 'true',
            "queue_id": user['call_info'].get('queue_id', '')
        })
        return resp_body


if __name__ == "__main__":
    # config logger
    config_logger('logs/phone')

    # parse sys.argv
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=59999, type=int)
    # set 2 to enable Interact Mode
    parser.add_argument('-i', '--interruptable', action='store_true',
                        help='whether the user can interrupt when bot is speaking')
    parser.add_argument('-l', '--lock_before_fwd', action='store_true',
                        help='Whether to lock the queue of agent before call forwarding')
    parser.add_argument('-c', '--config', default="config_phone.yml", type=str)
    args = parser.parse_args()

    # builtin_conf
    conf = {}
    builtin_config_file = os.path.join(os.path.dirname(__file__), 'config', 'cfg_server_phone.yml')
    if os.path.exists(builtin_config_file):
        with open(builtin_config_file, 'r', encoding='utf-8') as f:
            conf = yaml.safe_load(f)

    # custom config
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            custom_conf = yaml.safe_load(f)
            conf.update(custom_conf)

    # config port
    conf.setdefault("port", args.port)

    # config db
    db = None
    if 'postgresql' not in conf:
        logging.warning('postgresql database config is not available.')
        db = None
    else:
        for _ in range(5):
            try:
                db = PostgreSQLWrapper(conf['postgresql'])
                logging.info('connect to the postgresql database successfully.')
                break
            except:
                logging.warning('fail to connect to the postgresql database.')
                time.sleep(0.5)


    # config bot
    conf.setdefault('bot', {})
    conf['bot'].setdefault('interruptable', args.interruptable)
    conf['bot'].setdefault('lock_before_fwd', args.lock_before_fwd)

    # config asr
    conf.setdefault('asr', {})

    # load bot
    logging.info('loading bot...')
    bot = Bot(interruptable=conf['bot']['interruptable'])
    logging.info('bot loaded.')

    # app
    application = tornado.web.Application([
        (r"/", MainHandler, dict(bot=bot, db=db, bot_conf=conf['bot'], asr_conf=conf['asr'])),
    ])
    application.listen(conf['port'])
    logging.info('listening on 127.0.0.1:%s...' % conf['port'])
    tornado.ioloop.IOLoop.current().start()
