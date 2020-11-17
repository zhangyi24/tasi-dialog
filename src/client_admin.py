# coding=utf-8
import requests
import copy
import logging

def post(url, req_body):
    resp = requests.post(url=url, json=req_body)
    logging.info(resp.elapsed, resp.json() if resp.content else {})


if __name__ == '__main__':
    host = "127.0.0.1"
    port = "39999"
    url = f"http://{host}:{port}/kb"
    for req_body in [{}, {"action": "disable_knowledges"}, {"action": "disable_knowledge"}]:
        post(url, req_body)

