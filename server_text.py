# coding=utf-8
import json
import argparse
import datetime
import logging
import logging.config
import copy
import collections

import yaml
import tornado.ioloop
import tornado.httpclient
import tornado.escape
import tornado.web

from agent import Bot

RESPONSE_BODY_9 = {
	"ret": 0,
	"userid": "",
	"outaction": '9',
	"outparams": {
		"call_id": "",
		"inter_idx": "",
		"model_type": "",
		"prompt_text": "",
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

class MainHandler(tornado.web.RequestHandler):
	def initialize(self, bot):
		self.bot = bot
	
	def prepare(self):
		logging.info('req_headers: %s' % dict(self.request.headers))
		self.req_body = json.loads(self.request.body) if self.request.body else {}
		logging.info('req_body: %s' % self.req_body)
		self.set_header(name='Content-Type', value='application/json; charset=UTF-8')
	
	def get(self):
		self.write('SPMIBOT')
	
	def post(self):
		if self.req_body['inaction'] == 8:
			user_info = self.req_body['inparams']['user_info']
			bot_resp = self.bot.init(user_id=self.req_body['userid'], user_info=user_info,
			                         call_info=self.req_body['inparams'])
			user = self.bot.users[self.req_body['userid']]
			user['inter_idx'] = '1'
			user['resp_queue'] = collections.deque()
			resp_body = self.generate_resp_body_interact(user, bot_resp['content'])
		
		elif self.req_body['inaction'] == 9:
			if self.req_body['userid'] not in self.bot.users:
				logging.info('there is no user whose user_id is \'%s\'.' % self.req_body['userid'])
				return
			# 根据user_id获取用户信息
			user = self.bot.users[self.req_body['userid']]
			# 用户主动挂断
			if self.req_body['inparams']['flow_result_type'] == '3' and self.req_body['inparams']['input'] == 'hangup':
				resp_body = self.generate_resp_body_hangup(user)
			# 有待完成指令
			elif user['resp_queue']:
				resp_body = user['resp_queue'].popleft()
			else:
				user['inter_idx'] = str(int(self.req_body['inparams']['inter_idx']) + 1)
				input = ''
				if self.req_body['inparams']['flow_result_type'] in ['1', '2']:
					input = self.req_body['inparams']['input']
				bot_resp, user['call_status'] = self.bot.response(self.req_body['userid'], input)
				# 正常交互
				if user['call_status'] == 'on':
					resp_body = self.generate_resp_body_interact(user, bot_resp['content'])
				
				# 机器人发起挂断或转人工
				else:
					resp_body = self.generate_resp_body_interact(user, bot_resp['content'], input=False)
					user['resp_queue'].append(self.generate_resp_body_hangup(user))

		
		self.write(json.dumps(resp_body, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
		self.bot.users[resp_body['userid']]['last_resp_body'] = resp_body
		if resp_body['outaction'] == '10':
			del self.bot.users[resp_body['userid']]
		logging.info('resp_headers: %s' % dict(self._headers))
		logging.info('resp_body: %s' % resp_body)
	
	def generate_resp_body_interact(self, user, prompt, input=True, timeout='5'):
		resp_body = copy.deepcopy(RESPONSE_BODY_9)
		resp_body.update({"userid": self.req_body['userid']})
		resp_body["outparams"].update({
			"call_id": user["call_info"].get('call_id', ''),
			"inter_idx": user['inter_idx'],
			"model_type": '11' if input else '10',
			"prompt_text": prompt,
			"timeout": timeout if input else '0'
		})
		return resp_body
	
	def generate_resp_body_hangup(self, user):
		resp_body = copy.deepcopy(RESPONSE_BODY_10)
		resp_body.update({"userid": self.req_body['userid']})
		resp_body["outparams"].update({
			"call_id": user['call_info'].get('call_id', ''),
			"call_sor_id": user['call_info'].get('call_sor_id', ''),
			"start_time": user['call_info'].get('start_time', ''),
			"end_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3]
		})
		return resp_body


if __name__ == "__main__":
	# parse sys.argv
	parser = argparse.ArgumentParser()
	parser.add_argument('-p', '--port', default=59998, type=int)
	args = parser.parse_args()
	conf = {}
	with open("config_text.yml") as f:
		conf = yaml.safe_load(f)
	if "logging" in conf:
		logging.config.dictConfig(conf["logging"])
	
	# bot
	logging.info('loading bot...')
	bot = Bot()
	logging.info('bot loaded.')
	# app
	application = tornado.web.Application([
		(r"/", MainHandler, dict(bot=bot)),
	])
	application.listen(args.port)
	logging.info('listening on 127.0.0.1:%s...' % args.port)
	tornado.ioloop.IOLoop.current().start()
