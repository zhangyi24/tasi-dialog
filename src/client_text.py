# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""A simple client for testing server(text version)"""

import datetime
import requests
import argparse
import os
import yaml

from utils.config import merge_config


def get_req_body_init(call_id, call_sor_id, user_info):
    req_body = {
        'userid': call_id,
        'inaction': 8,
        'inparams': {
            'call_id': call_id,
            'call_sor_id': call_sor_id,
            'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3],
            'user_info': user_info
        }
    }
    return req_body


def get_req_body_speak_hangup(call_id, inter_idx):
    req_body = {
        'userid': call_id,
        'inaction': 9,
        'inparams': {
            'call_id': call_id,
            'inter_idx': inter_idx,
            'flow_result_type': '3',
            'input': '',
            'inter_no': '',
        }
    }
    return req_body


def get_req_body_speak_listen(call_id, inter_idx, input, inter_no=''):
    req_body = {
        'userid': call_id,
        'inaction': 9,
        'inparams': {
            'call_id': call_id,
            'inter_idx': inter_idx,
            'flow_result_type': '1',
            'input': input,
            'inter_no': inter_no
        }
    }
    return req_body


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
    conf_text = conf["text"]

    # url
    server_url = 'http://%s:%s' % (args.ip, conf_text['port'])

    # call_info and user_info
    call_id = '123'
    call_sor_id = '130****1234'
    user_info = 'dummy#val0#val1#val2#val3#val4#val5#val6#val7#val8#val9'

    # run
    while True:
        req_body = get_req_body_init(call_id, call_sor_id, user_info)
        resp = requests.post(url=server_url, json=req_body)
        resp_body = resp.json() if resp.content else {}
        while resp_body['outaction'] != '10':
            assert resp_body['outaction'] == '9'
            assert resp_body['outparams']['model_type'] in ['11', '10']
            print('bot:\t%s' % resp_body['outparams']['prompt_text'])
            if resp_body['outparams']['model_type'] == '11':
                req_body = get_req_body_speak_listen(call_id,
                                                resp_body['outparams']['inter_idx'],
                                                input('user:\t'))
            if resp_body['outparams']['model_type'] == '10':
                req_body = get_req_body_speak_hangup(call_id, resp_body['outparams']['inter_idx'])
            resp = requests.post(url=server_url, json=req_body)
            resp_body = resp.json() if resp.content else {}
        if input('continue? (Y?n)').lower() == 'n':
            break
