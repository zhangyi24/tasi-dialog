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


def get_req_body_init(call_id, call_sor_id, user_info, entrance_id, queue_id, strategy_params):
    req_body = {
        'userid': call_id,
        'inaction': 8,
        'inparams': {
            'call_id': call_id,
            'call_sor_id': call_sor_id,
            'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3],
            'extend': user_info,
            'entrance_id': entrance_id,
            'queue_id': queue_id,
            'strategy_params': strategy_params
        }
    }
    return req_body


def get_req_body_9(call_id, inter_idx, user_input=''):
    req_body = {
        'userid': call_id,
        'inaction': 9,
        'inparams': {
            'call_id': call_id,
            'inter_idx': inter_idx,
            'begin_play': '2020-03-14 22:22:37909',
            'end_play': '2020-03-14 22:22:47838',
            'result_time': '2020-03-14 22:22:47838',
            'flow_result_type': '1',
            'input': user_input,
            'inter_no': '2020-03-14 22:22:37909',
            'org': '',
            'grammar': '',
            'newsess': '',
            'res_node_lst': '',
            'res_parse_mode': '',
            'extended_field': ''
        }
    }
    return req_body


def get_req_body_11(call_id, inter_idx):
    req_body_11 = {
        "userid": call_id,
        "inaction": 11,
        "inparams": {
            "call_id": call_id,
            "inter_idx": inter_idx,
            "begin_trans": "转移的开始时间",
            "end_trans": "转移的结束时间",
            "trans_result": "1"
        }
    }
    return req_body_11


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
    conf_text = conf["phone"]

    # url
    server_url = 'http://%s:%s' % (args.ip, conf_text['port'])

    # call_info and user_info
    call_id = '123'
    call_sor_id = '130****1234'
    user_info = 'dummy#val0#val1#val2#val3#val4#val5#val6#val7#val8#val9'
    entrance_id = "2"
    queue_id = "52"
    strategy_params = "2306#2429719#441"

    # run
    while True:
        req_body = get_req_body_init(call_id, call_sor_id, user_info, entrance_id, queue_id, strategy_params)
        resp = requests.post(url=server_url, json=req_body)
        resp_body = resp.json() if resp.content else {}
        while True:
            if resp_body['outaction'] == '9':
                user_input = ''
                if resp_body['outparams']['model_type'][0] == "1":
                    print('bot:\t%s' % resp_body['outparams']['prompt_text'])
                if "1" in resp_body['outparams']['model_type'][1:3]:
                    user_input = input('user:\t')
                req_body = get_req_body_9(call_id, resp_body['outparams']['inter_idx'], user_input)

            elif resp_body['outaction'] == '11':
                req_body = get_req_body_11(call_id, resp_body['outparams']['inter_idx'])
            else:
                break
            resp = requests.post(url=server_url, json=req_body)
            resp_body = resp.json() if resp.content else {}
        if input('continue? (Y?n)').lower() == 'n':
            break
