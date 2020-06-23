# coding=utf-8

import json
import glob
import os
import copy
import time
import logging
import collections

from nlu.nlu import NLUManager
from dm import cond_judge
from nlg import response_process
from dialog_config import functions


class Bot(object):
    def __init__(self, interact_mode='1'):
        # import config files
        # flows
        self.interact_mode = interact_mode
        self.flows = {}
        for file in glob.glob('dialog_config/flows/*.json'):
            flow_name = os.path.basename(file).split('.')[0]
            with open(file, 'r', encoding='utf-8') as f:
                self.flows[flow_name] = json.load(f)

        # intent_flow_mapping
        self.intent_flow_mapping = {}
        for flow_name, flow in self.flows.items():
            if 'intent' in flow:
                self.intent_flow_mapping[flow['intent']] = flow_name
        # intents
        with open('dialog_config/intents.json', 'r', encoding='utf-8') as f:
            self.intents = json.load(f)
        # entities
        self.entities = {}
        with open('dialog_config/builtin_entities.json', 'r', encoding='utf-8') as f:
            self.entities['builtin'] = json.load(f)
        with open('dialog_config/user_entities.json', 'r', encoding='utf-8') as f:
            self.entities['user'] = json.load(f)
        # global_vars
        with open('dialog_config/global_vars.json', 'r', encoding='utf-8') as f:
            g_vars_cfg = json.load(f)
            self.g_vars = g_vars_cfg['g_vars']
            self.g_vars_need_init = g_vars_cfg['g_vars_need_init']  # 需要初始值来初始化的全局变量。实例化一个机器人时需要传入这些变量的初始值

        # functions
        from dialog_config import functions

        # templates
        with open('dialog_config/corpus/templates.json', 'r', encoding='utf-8') as f:
            self.templates = json.load(f)
        # stop_words
        with open('dialog_config/stop_words.txt', 'r', encoding='utf-8') as f:
            self.stop_words = f.read().strip().split()
        # service language
        with open('dialog_config/service_language.json', 'r', encoding='utf-8') as f:
            self.service_language = json.load(f)
        # results of calls for analysis
        with open('dialog_config/results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
            self.results_code = results['results_code']
            self.init_results = results['init_results']

        # init nlu_manager
        self.nlu_manager = NLUManager(self.templates, self.intents, self.entities, self.stop_words)
        self.nlu_manager.intent_recognition('%%初始化%%')  # 第一次识别会比较慢，所以先识别一次。

        self.users = {}

    def init(self, user_id, user_info, call_info):
        self.users[user_id] = {
            "user_id": user_id,
            "g_vars": copy.deepcopy(self.g_vars),
            "node_stack": [],
            "call_info": call_info,
            "call_status": 'on',
            "history": [],
            "results": [],
            "task_id": call_info['strategy_params'].split('#')[0]
        }
        self.users[user_id]['g_vars']['intent'] = None
        if len(self.g_vars_need_init) != len(user_info):
            logging.error("The length of 'g_vars_need_init' must be equal to the length of 'user_info': %s != %s",
                          len(self.g_vars_need_init), len(user_info))
        else:
            self.users[user_id]['g_vars'].update(dict(zip(self.g_vars_need_init, user_info)))
        resp = {'content': response_process(self.service_language['greeting'], self.users[user_id]['g_vars']),
                'allow_interrupt': self.interact_mode == '2', 'input_channel': '10'}
        return resp

    def response(self, user_id, user_utter):
        user = self.users[user_id]
        resp = {'content': None, 'allow_interrupt': self.interact_mode == '2', 'input_channel': '10'}
        g_vars = self.users[user_id]['g_vars']
        node_stack = self.users[user_id]['node_stack']
        intent = self.nlu_manager.intent_recognition(user_utter)
        g_vars['intent'] = intent
        if intent is not None:
            if not node_stack or (
                    intent in self.intent_flow_mapping and self.intent_flow_mapping[intent] != node_stack[0][
                'flow_name']):
                node_stack.clear()
                node_stack.append({'flow_name': self.intent_flow_mapping[intent], 'node_id': '0'})

        while not resp['content']:
            if not node_stack:
                resp['content'] = response_process(self.service_language['pardon'], g_vars)
                break
            # print(g_vars, node_stack)
            current_flow = self.flows[node_stack[-1]['flow_name']]
            current_node = current_flow['nodes'][node_stack[-1]['node_id']]
            # todo: 每经过一个节点就把该节点的结果追加到results后，有没有更合理的记录对话结果的方法
            user['results'].extend(current_node.get('results', []))

            if current_node['type'] == 'branch':
                pass

            elif current_node['type'] == 'assignment':
                for item in current_node['assignments']:
                    g_vars[item['g_vars']] = item['value']

            elif current_node['type'] == 'response':
                resp['content'] = response_process(current_node['response'], g_vars)

            elif current_node['type'] == 'flow':
                if 'return' not in node_stack[-1]:
                    node_stack[-1]['return'] = True
                    node_stack.append({'flow_name': current_node['flowName'], 'node_id': '0'})
                    continue
                else:
                    del node_stack[-1]['return']

            elif current_node['type'] == 'slot_filling':
                if 'slots_status' not in node_stack[-1]:
                    node_stack[-1]['slots_status'] = self.nlu_manager.slots_status_init(current_node['slots'],
                                                                                        user_utter, g_vars)
                resp['content'], finish = self.nlu_manager.slots_filling(node_stack[-1]['slots_status'], user_utter,
                                                                         g_vars)
                if not finish:
                    continue
                else:
                    del node_stack[-1]['slots_status']

            elif current_node['type'] == 'function':
                exec('g_vars["func_return"] = ' + 'functions.' + current_node['funcName'] + '(user_utter, g_vars)')

            # dm
            assert 'dm' in current_node
            for case in current_node['dm']:
                cond = case['cond']
                cond_is_true = True if cond is True else cond_judge(cond, data={"global": g_vars})
                if cond_is_true or cond == 'else':
                    node_stack[-1]['node_id'] = case['nextNode']
                    next_node = current_flow['nodes'][case['nextNode']]
                    if next_node['type'] == 'return':
                        node_stack.pop()
                    elif next_node['type'] == 'exit':
                        if next_node['todo'] == 'hangup':
                            user['call_status'] = 'hangup'
                        elif next_node['todo'] == 'fwd':
                            user['call_status'] = 'fwd'
                        node_stack.clear()
                    if 'response' in case:
                        resp['content'] = response_process(case['response'], g_vars)
                    break
        return resp, user['call_status']

    def convert_results_to_code(self, user):
        if not user['results']:
            user['results'] = self.init_results
        user['results'] = [self.results_code[res] for res in user['results']]
        return user['results']
