# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""A simple client for testing server(phone version)"""

import datetime
import requests
import argparse
import os
import yaml
# import readline

from utils.config import merge_config

class Client(object):
    def __init__(self, call_id='123', call_sor_id='130****1234', user_info=None, entrance_id='0', queue_id='0', strategy_params='0#0#0'):
        self.call_id = call_id
        self.call_sor_id = call_sor_id
        self.user_info = '#'.join(f'val{i}' for i in range(10)) if user_info is None else user_info
        self.entrance_id = entrance_id
        self.queue_id = queue_id
        self.strategy_params = strategy_params
        self.hungup = False

    def get_req_body_init(self):
        req_body = {
            'userid': self.call_id,
            'inaction': 8,
            'inparams': {
                'call_id': self.call_id,
                'call_sor_id': self.call_sor_id,
                'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3],
                'extend': self.user_info,
                'entrance_id': self.entrance_id,
                'queue_id': self.queue_id,
                'strategy_params': self.strategy_params
            }
        }
        return req_body


    def get_req_body_9(self, inter_idx, user_input=''):
        req_body = {
            'userid': self.call_id,
            'inaction': 9,
            'inparams': {
                'call_id': self.call_id,
                'inter_idx': inter_idx,
                'begin_play': '',
                'end_play': '',
                'result_time': '',
                'flow_result_type': '1',
                'input': user_input,
                'inter_no': '',
                'org': '',
                'grammar': '',
                'newsess': '',
                'res_node_lst': '',
                'res_parse_mode': '',
                'extended_field': ''
            }
        }
        return req_body


    def get_req_body_11(self, inter_idx):
        req_body_11 = {
            "userid": self.call_id,
            "inaction": 11,
            "inparams": {
                "call_id": self.call_id,
                "inter_idx": inter_idx,
                "begin_trans": "",
                "end_trans": "",
                "trans_result": "1"
            }
        }
        return req_body_11

    def generate_req_body(self, resp_body=None):
        req_body = None
        if resp_body is None:
            req_body = self.get_req_body_init()
            self.hungup = False
        elif resp_body['outaction'] == '9':
            user_input = ''
            if resp_body['outparams']['model_type'][0] == "1":
                print('bot:\t%s' % resp_body['outparams']['prompt_text'])
            if "1" in resp_body['outparams']['model_type'][1:3]:
                user_input = input('user:\t')
            req_body = self.get_req_body_9(resp_body['outparams']['inter_idx'], user_input)
        elif resp_body['outaction'] == '11':
            req_body = self.get_req_body_11(resp_body['outparams']['inter_idx'])
        elif resp_body['outaction'] == '10':
            self.hungup = True
        return req_body


    def is_hungup(self):
        return bool(self.hungup)


if __name__ == '__main__':
    # parse sys.argv
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', default='127.0.0.1', type=str)
    args = parser.parse_args()

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
    conf_phone = conf["phone"]

    # url
    server_url = 'http://%s:%s' % (args.ip, conf_phone['port'])

    # run
    while True:
        client = Client()
        req_body = client.generate_req_body()
        resp = requests.post(url=server_url, json=req_body)
        resp_body = resp.json() if resp.content else {}
        while not client.hungup:
            req_body = client.generate_req_body(resp_body)
            if client.hungup:
                break
            resp = requests.post(url=server_url, json=req_body)
            resp_body = resp.json() if resp.content else {}
        if input('continue? (Y?n)').lower() == 'n':
            break
