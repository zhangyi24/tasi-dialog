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

RESPONSE_BODY_9 = {
	"ret": 0,
	"userid": "",
	"outaction": '9',
	"outparams": {
		"call_id": "",
		"inter_idx": "",
		"model_type": "",
		"prompt_text": "",
		"prompt_src": "",
		"timeout": ""
	}
}

RESPONSE_BODY_10 = {
	"ret": 0,
	"userid": "",
	"outaction": '10',
	"outparams": {
		"call_id": "",
		"call_sor_id": "",
		"start_time": "",
		"end_time": ""
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

class MainHandler(tornado.web.RequestHandler):
	def initialize(self, bot, bot_conf):
		self.bot = bot
		self.bot_conf = bot_conf
	
	def prepare(self):
		logging.info('req_headers: %s' % dict(self.request.headers))
		self.req_body = json.loads(self.request.body) if self.request.body else {}
		logging.info('req_body: %s' % self.req_body)
		self.set_header(name='Content-Type', value='application/json; charset=UTF-8')
	
	def get(self):
		self.write('SPMIBOT')
	
	def post(self):
		resp_body = None
		if self.req_body['inaction'] == 8:
			# 处理扩展字段
			user_info = self.req_body['inparams']['extend'].split('#')[1:]
			# 处理通话参数
			call_info = copy.deepcopy(self.req_body['inparams'])
			if not self.bot_conf["fwd"]["queue_id_updatable"]:
				call_info["queue_id"] = self.bot_conf["fwd"]["queue_id"]
			self.bot.init(call_id=self.req_body['userid'], user_info=user_info,
									 call_info=call_info)
			call = self.bot.calls[self.req_body['userid']]
			call['inter_idx'] = '1'
			call['resp_queue'] = collections.deque()

			# 获取开场白
			bot_resp, call['call_status'] = self.bot.greeting(call_id=self.req_body['userid'])
			# 正常交互
			resp_body = self.generate_resp_body(call, bot_resp)
		
		elif self.req_body['inaction'] == 9:
			if self.req_body['userid'] not in self.bot.calls:
				logging.info('there is no call whose userid is \'%s\'.' % self.req_body['userid'])
				return
			# 根据userid获取呼叫信息
			call = self.bot.calls[self.req_body['userid']]
			# 用户主动挂断
			if self.req_body['inparams']['flow_result_type'] == '3' and self.req_body['inparams']['input'] == 'hangup':
				call['resp_queue'].clear()
				resp_body = self.generate_resp_body_hangup(call)
			# 有待完成指令
			elif call['resp_queue']:
				resp_body = call['resp_queue'].popleft()
			else:
				call['inter_idx'] = str(int(self.req_body['inparams']['inter_idx']) + 1)
				input = ''
				if self.req_body['inparams']['flow_result_type'] in ['1', '2']:
					input = self.req_body['inparams']['input']
				call['history'].append('用户：' + input)
				bot_resp, call['call_status'] = self.bot.response(self.req_body['userid'], input)
				resp_body = self.generate_resp_body(call, bot_resp)

		elif self.req_body['inaction'] == 11:
			call = self.bot.calls[self.req_body['userid']]
			trans_success = self.req_body['inparams']['trans_result'] == '1'
			resp_body = self.generate_resp_body_hangup(call)  # 无论是否转移成功，这通电话已经结束。

		
		self.write(json.dumps(resp_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
		self.bot.calls[resp_body['userid']]['last_resp_body'] = resp_body
		if resp_body['outaction'] == '10':
			del self.bot.calls[resp_body['userid']]
		logging.info('resp_headers: %s' % dict(self._headers))
		logging.info('resp_body: %s' % resp_body)
	
	def generate_resp_body_interact(self, call, bot_resp, input=True, timeout='5'):
		call['history'].append('机器人：' + bot_resp['content'])
		resp_body = copy.deepcopy(RESPONSE_BODY_9)
		resp_body.update({"userid": self.req_body['userid']})
		resp_body["outparams"].update({
			"call_id": call["call_info"].get('call_id', ''),
			"inter_idx": call['inter_idx'],
			"model_type": '11' if input else '10',
			"prompt_text": bot_resp['content'],
			"prompt_src": bot_resp['src'],
			"timeout": timeout if input else '0'
		})
		return resp_body
	
	def generate_resp_body_hangup(self, call):
		resp_body = copy.deepcopy(RESPONSE_BODY_10)
		resp_body.update({"userid": self.req_body['userid']})
		resp_body["outparams"].update({
			"call_id": call['call_info'].get('call_id', ''),
			"call_sor_id": call['call_info'].get('call_sor_id', ''),
			"start_time": call['call_info'].get('start_time', ''),
			"end_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3]
		})
		return resp_body

	def generate_resp_body_fwd(self, call):
		resp_body = copy.deepcopy(RESPONSE_BODY_11)
		resp_body.update({"userid": self.req_body['userid']})
		resp_body["outparams"].update({
			"call_id": call['call_info'].get('call_id', ''),
			"inter_idx": call['inter_idx'],
			"call_sor_id": call['call_info'].get('call_sor_id', ''),
			"queue_id": call['call_info'].get('queue_id', '')
		})
		return resp_body

	def generate_resp_body(self, call, bot_resp):
		# 正常交互
		if call['call_status'] == 'on':
			resp_body = self.generate_resp_body_interact(call, bot_resp)
		# 机器人发起挂断
		elif call['call_status'] == 'hangup':
			resp_body = self.generate_resp_body_interact(call, bot_resp, input=False)
			call['resp_queue'].append(self.generate_resp_body_hangup(call))
		# 机器人发起呼叫转移
		elif call['call_status'] == 'fwd':
			resp_body = self.generate_resp_body_interact(call, bot_resp, input=False)
			call['resp_queue'].append(self.generate_resp_body_fwd(call))
		return resp_body


def initbot():
	# config logger
	config_logger('logs/text')

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
	merge_config(conf, custom_conf) # merge custom_conf to default_conf
	conf_text = conf["text"]
	
	# bot
	logging.info('loading bot...')
	bot = Bot(bot_config=conf["bot"])
	logging.info('bot loaded.')
	
	return bot, conf

if __name__ == "__main__":
	bot, conf = initbot()
	conf_text = conf["text"]
	# app
	application = tornado.web.Application([
		(r"/", MainHandler, dict(bot=bot, bot_conf=conf_text['bot'])),
	])
	application.listen(conf_text['port'])
	logging.info('listening on 127.0.0.1:%s...' % conf_text['port'])
	tornado.ioloop.IOLoop.current().start()
