# coding=utf-8

import json
import glob
import os
import copy
import time
import logging
import sys
import collections

from nlu import NLUManager
from dm import cond_judge
from nlg import response_process
sys.path.append(".")
functions_path = 'dialog_config/functions.py'
if os.path.exists(functions_path):
    from dialog_config import functions


class ResultsTracker(object):
    def __init__(self, results_code, init_results):
        self.results_code = results_code
        self.init_results = init_results

    def convert_results_to_codes(self, results):
        codes = [self.results_code[res] for res in results]
        return codes


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
        self.intents = {}
        intents_config_path = 'dialog_config/intents.json'
        if os.path.exists(intents_config_path):
            with open('dialog_config/intents.json', 'r', encoding='utf-8') as f:
                self.intents = json.load(f)
        # value_sets
        # builtin value_sets
        self.value_sets = {}
        builtin_value_sets_file_path = os.path.join(os.path.dirname(__file__), 'builtin_value_sets.json')
        with open(builtin_value_sets_file_path, 'r', encoding='utf-8') as f:
            self.value_sets['builtin'] = json.load(f)
        # custom value_sets
        self.value_sets['user'] = {}
        custom_value_sets_config_path = 'dialog_config/value_sets.json'
        if os.path.exists(custom_value_sets_config_path):
            with open(custom_value_sets_config_path, 'r', encoding='utf-8') as f:
                self.value_sets['user'] = json.load(f)
        # builtin_vars
        self.builtin_vars = {'intent': None, 'func_return': None, 'last_response': None}
        # global_vars
        self.g_vars = {}
        self.g_vars_need_init = []
        g_vars_config_path = 'dialog_config/global_vars.json'
        if os.path.exists(g_vars_config_path):
            with open(g_vars_config_path, 'r', encoding='utf-8') as f:
                g_vars_cfg = json.load(f)
                self.g_vars = g_vars_cfg['g_vars']
                self.g_vars_need_init = g_vars_cfg['g_vars_need_init']  # 需要初始值来初始化的全局变量。实例化一个机器人时需要传入这些变量的初始值

        # templates
        self.templates = {}
        templates_path = 'dialog_config/corpus/templates.json'
        if os.path.exists(templates_path):
            with open('dialog_config/corpus/templates.json', 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        # stop_words
        self.stop_words = []
        stop_words_path = 'dialog_config/stop_words.txt'
        if os.path.exists(stop_words_path):
            with open(stop_words_path, 'r', encoding='utf-8') as f:
                self.stop_words = f.read().strip().split()
        # service language
        with open('dialog_config/service_language.json', 'r', encoding='utf-8') as f:
            self.service_language = json.load(f)
        # results of calls for analysis
        self.results_tracker = None
        results_tracker_config_file = 'dialog_config/results.json'
        if os.path.exists(results_tracker_config_file):
            with open(results_tracker_config_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                self.results_tracker = ResultsTracker(results['results_code'], results['init_results'])

        # init nlu_manager
        checkpoints_dir = 'checkpoints/intent'
        label_dir = 'datasets/intent'
        self.nlu_manager = NLUManager(checkpoints_dir, label_dir, self.templates, self.intents, self.value_sets, self.stop_words)
        self.nlu_manager.intent_recognition('%%初始化%%')  # 第一次识别会比较慢，所以先识别一次。

        self.users = {}

    def init(self, user_id, user_info, call_info, task_id=-1):
        self.users[user_id] = {
            "user_id": user_id,
            "g_vars": copy.deepcopy(self.g_vars),
            "builtin_vars": copy.deepcopy(self.builtin_vars),
            "node_stack": [],
            "main_flow_node": {},
            "call_info": call_info,
            "call_status": 'on',
            "history": [],
            "results": self.results_tracker.init_results if self.results_tracker else [],
            "task_id": task_id
        }
        # main_flow_node
        if 'main' in self.flows:
            self.users[user_id]['main_flow_node'] = {"node_id": "0"}
        # use user_info to init some global variables
        if len(self.g_vars_need_init) != len(user_info):
            logging.warning("The length of 'g_vars_need_init' must be equal to the length of 'user_info': %s != %s",
                          len(self.g_vars_need_init), len(user_info))
        self.users[user_id]['g_vars'].update(dict(zip(self.g_vars_need_init, user_info)))
        # return greeting as the bot's response
        resp = {'content': response_process(self.service_language['greeting'], self.users[user_id]['g_vars'], self.users[user_id]['builtin_vars']),
                'allow_interrupt': self.interact_mode == '2', 'input_channel': '10'}
        return resp

    def response(self, user_id, user_utter):
        user = self.users[user_id]
        resp = {'content': None, 'allow_interrupt': self.interact_mode == '2', 'input_channel': '10'}
        g_vars = self.users[user_id]['g_vars']
        builtin_vars = self.users[user_id]['builtin_vars']
        node_stack = self.users[user_id]['node_stack']
        main_flow_node = self.users[user_id]['main_flow_node']
        # 意图识别
        intent = self.nlu_manager.intent_recognition(user_utter)
        builtin_vars['intent'] = intent
        # 根据意图识别结果调整node_stack
        if intent is not None:
            if not node_stack or (
                    intent in self.intent_flow_mapping and self.intent_flow_mapping[intent] != node_stack[0][
                'flow_name']):
                node_stack.clear()
                node_stack.append({'flow_name': self.intent_flow_mapping[intent], 'node_id': '0'})

        # 执行流程，直到得到response
        while not resp['content']:
            # get current node
            # print(g_vars, node_stack)
            if node_stack:
                current_flow = self.flows[node_stack[-1]['flow_name']]
                current_node = current_flow['nodes'][node_stack[-1]['node_id']]
            elif main_flow_node:
                current_flow = self.flows['main']
                current_node = current_flow['nodes'][main_flow_node['node_id']]
            else:
                resp['content'] = response_process(self.service_language['pardon'], g_vars, builtin_vars)
                break

            # log results
            # todo: 每经过一个节点就把该节点的结果追加到results后，有没有更合理的记录对话结果的方法
            user['results'].extend(current_node.get('results', []))

            # branch
            if current_node['type'] == 'branch':
                pass

            # assignment
            elif current_node['type'] == 'assignment':
                for item in current_node['assignments']:
                    g_vars[item['g_vars']] = item['value']

            # response
            elif current_node['type'] == 'response':
                resp['content'] = response_process(current_node['response'], g_vars, builtin_vars)

            # flow
            elif current_node['type'] == 'flow':
                node_info = node_stack[-1] if node_stack else main_flow_node
                # 非主流程
                if node_stack:
                    if 'return' not in node_info:
                        node_info['return'] = False
                        node_stack.append({'flow_name': current_node['flowName'], 'node_id': '0'})
                        continue
                    else:
                        del node_info['return']

            # slot_filling
            elif current_node['type'] == 'slot_filling':
                node_info = node_stack[-1] if node_stack else main_flow_node
                if 'slots_status' not in node_info:
                    node_info['slots_status'] = self.nlu_manager.slots_status_init(current_node['slots'],
                                                                                        user_utter, g_vars)
                resp['content'], finish = self.nlu_manager.slots_filling(node_info['slots_status'], user_utter,
                                                                         g_vars)
                if not finish:
                    continue
                else:
                    del node_info['slots_status']

            # function
            elif current_node['type'] == 'function':
                exec('builtin_vars["func_return"] = ' + 'functions.' + current_node['funcName'] + '(user_utter, g_vars)')

            # dm
            assert 'dm' in current_node
            for case in current_node['dm']:
                cond = case['cond']
                cond_is_true = True if cond is True else cond_judge(cond, data={"global": g_vars, "builtin": builtin_vars})
                if cond_is_true or cond == 'else':
                    # 处理nextNode。分当前流程是主流程和非主流程两种情况处理
                    # 非主流程
                    if node_stack:
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
                    # 主流程
                    else:
                        main_flow_node = {'node_id': case['nextNode']}
                        next_node = current_flow['nodes'][case['nextNode']]
                        if next_node['type'] == 'return':
                            main_flow_node = {}
                        elif next_node['type'] == 'exit':
                            if next_node['todo'] == 'hangup':
                                user['call_status'] = 'hangup'
                            elif next_node['todo'] == 'fwd':
                                user['call_status'] = 'fwd'
                            main_flow_node = {}

                    # 处理response
                    if 'response' in case:
                        resp['content'] = response_process(case['response'], g_vars, builtin_vars)
                    break
        builtin_vars['last_response'] = resp['content']
        return resp, user['call_status']

    def convert_results_to_codes(self, user):
        user['results'] = self.results_tracker.convert_results_to_codes(user['results'])
        return user['results']
