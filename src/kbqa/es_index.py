#coding=utf-8

import yaml
import os
import sys

from es import ES

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
from utils.config import merge_config

if __name__ == "__main__":
    # builtin_conf
    builtin_config_file = os.path.join(os.path.dirname(__file__), "..", 'config', 'config.yml')
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
    conf_kb = conf["bot"]["kb"]

    addr = conf_kb["es_addr"]
    bot_name = os.path.basename(os.getcwd())
    index = conf_kb["es_index_prefix"] + "-" + bot_name
    synonyms_path = os.path.abspath(os.path.realpath("qa/synonym.txt"))
    synonyms = []
    if os.path.exists(synonyms_path):
        with open(synonyms_path, "r", encoding="utf-8") as f:
            synonyms = f.read().strip().split("\n")
    print(f"synonyms: {synonyms}")
    es = ES(addr, index, synonyms)
    es.index_doc("qa/qa.json")
