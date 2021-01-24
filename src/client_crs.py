# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""A simple client for testing crs server"""

import requests
import argparse
import os
import yaml

from utils.config import merge_config
from client_text import Client as ClientText
from client_phone import Client as ClientPhone


if __name__ == '__main__':
    # parse sys.argv
    parser = argparse.ArgumentParser(description='CRS Client')
    parser.add_argument('-i', '--ip', default='127.0.0.1', type=str)
    parser.add_argument('-e', '--entrance_id', default="0", help="entrance id")
    parser.add_argument('-t', '--interface_type', default='text', type=str, help="interface type", choices=["text", "phone"])
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
    conf_crs = conf["crs"]

    # url
    server_url = 'http://%s:%s' % (args.ip, conf_crs['port'])

    # run
    while True:
        if args.interface_type == "text":
            client = ClientText(entrance_id=args.entrance_id)
        else:
            client = ClientPhone(entrance_id=args.entrance_id)
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
