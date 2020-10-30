# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""A simple client for testing server(text version)"""

import datetime
import requests
import argparse
import os
import yaml

from utils.config import merge_config


def get_req_body_init(call_id, message_id):
    req_body = {
        'callId': call_id,
        'messageId': message_id,
        'firstSign': "1",
        "modeType": "modeTypeVal",
        "mediaType": "mediaTypeVal",
        "reqSource": "reqSourceVal",
        "beginTime": "beginTimeVal",
        "messageProvider": "messageProviderVal",
        "channelCode": "channelCodeVal",
        "callerNo": "callerNoVal",
        "callerNoType": "callerNoTypeVal"
    }
    return req_body


def get_req_body_hangup(call_id, message_id):
    req_body = {
        'callId': call_id,
        'messageId': message_id,
        'firstSign': "2",
        "messageType": "03",
    }
    return req_body


def get_req_body_speak_listen(call_id, message_id, input):
    req_body = {
        'callId': call_id,
        'messageId': message_id,
        'firstSign': "2",
        "messageType": "01",
        "messageContent": input
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
    conf_text = conf["text-sgcc"]

    # url
    server_url = 'http://%s:%s' % (args.ip, conf_text['port'])

    # call_info and user_info
    call_id = '123'
    message_id = '12345'
    user_info = 'dummy#val0#val1#val2#val3#val4#val5#val6#val7#val8#val9'

    # run
    while True:
        req_body = get_req_body_init(call_id, message_id)
        resp = requests.post(url=server_url, json=req_body)
        resp_body = resp.json() if resp.content else {}
        while resp_body['actionType'] == '2':
            assert resp_body['actionContent'] in ['110', '101', '100']
            print('bot:\t%s' % resp_body['answerContent'])
            if resp_body['actionContent'] == '100':
                req_body = get_req_body_hangup(resp_body['callId'], resp_body['messageId'])
            else:
                req_body = get_req_body_speak_listen(resp_body['callId'],
                                                     resp_body['messageId'],
                                                     input('user:\t'))
            resp = requests.post(url=server_url, json=req_body)
            resp_body = resp.json() if resp.content else {}
        if input('continue? (Y?n)').lower() == 'n':
            break
