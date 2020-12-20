# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Bot for dialog server."""

import json
import glob
import os
import copy
import time
import logging
import sys
import collections
import yaml

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
    def __init__(self, interruptable=True, bot_config=None):
        # import config files
        # flows 
        self.interruptable = interruptable
        self.bot_config = {} if bot_config is None else bot_config
        self.flows = {}
        for file in glob.glob('dialog_config/flows/*.json'):
            flow_name = os.path.basename(file).split('.')[0]
            with open(file, 'r', encoding='utf-8') as f:
                self.flows[flow_name] = json.load(f)

        # intent_flow_mapping
        self.intent_flow_mapping = {}
        for flow_name, flow in self.flows.items():
            # 如果flow中有intent字段,关联入map,否则就是个子流程.
            if 'intent' in flow:
                self.intent_flow_mapping[flow['intent']] = flow_name
        # intents
        self.intents = {}
        intents_config_path = 'dialog_config/intents.json'
        if os.path.exists(intents_config_path):
            with open('dialog_config/intents.json', 'r', encoding='utf-8') as f:
                self.intents = json.load(f)
        # value_sets
        # builtin value_sets 内建Slot空间位置位于config/value_sets.json下
        self.value_sets = {}
        builtin_value_sets_file_path = os.path.join(os.path.dirname(__file__), 'config', 'value_sets.json')
        with open(builtin_value_sets_file_path, 'r', encoding='utf-8') as f:
            self.value_sets['builtin'] = json.load(f)
        # custom value_sets 用户自定义Slot空间位于dialog_config/value_sets.json下
        self.value_sets['user'] = {}
        custom_value_sets_config_path = 'dialog_config/value_sets.json'
        if os.path.exists(custom_value_sets_config_path):
            with open(custom_value_sets_config_path, 'r', encoding='utf-8') as f:
                self.value_sets['user'] = json.load(f)
        # builtin_vars 4个内建变量
        self.builtin_vars = {'intent': None, 'func_return': None, 'last_response': None, 'cnt_no_answer_succession': 0}
        # global_vars 全局变量
        self.g_vars = {}
        self.g_vars_need_init = []
        g_vars_config_path = 'dialog_config/global_vars.json'
        if os.path.exists(g_vars_config_path):
            with open(g_vars_config_path, 'r', encoding='utf-8') as f:
                g_vars_cfg = json.load(f)
                self.g_vars = g_vars_cfg['g_vars']
                self.g_vars_need_init = g_vars_cfg['g_vars_need_init']  # 需要初始值来初始化的全局变量。实例化一个机器人时需要传入这些变量的初始值

        # templates 模板
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
        self.nlu_manager = NLUManager(self.bot_config["intent_recognition"], self.templates, self.intents,
                                      self.value_sets, self.stop_words, self.bot_config["kb"], self.bot_config["kg"])
        self.nlu_manager.intent_recognition('测试意图识别')  # 第一次识别分类模型和匹配模型都会比较慢，所以先识别一次。
        self.nlu_manager.qa_kb('测试QA(KB)')  # 测试QA(KB)。
        self.nlu_manager.qa_kg('测试QA(KG)')  # 测试QA(KG)。

        self.users = {}

        self.input_channel_code_map = {
            "asr": "10",
            "keyboard": "01"
        }
        
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
        
    def greeting(self, user_id):
        user = self.users[user_id]
        # generate response
        resp = {'content': None, 'allow_interrupt': self.interruptable, 'input_channel': self.input_channel_code_map["asr"], 'src': ''}
        # return first response in main flow as the bot's response
        if 'main' in self.flows:
            resp, user['call_status'] = self.get_response_flow(user_id, user_utter=None)
            resp['src'] = 'flow'
        # return greeting as the bot's response
        if not resp['content']:
            resp['content'] = response_process(self.service_language['greeting'], self.users[user_id]['g_vars'],
                                               self.users[user_id]['builtin_vars'])
            resp['src'] = 'greeting'
        self.users[user_id]['builtin_vars']['last_response'] = resp['content']
        return resp, user['call_status']

    def response(self, user_id, user_utter):
        """生成机器人回复"""
        resp, call_status = self.get_response_flow(user_id, user_utter)
        g_vars = self.users[user_id]['g_vars']
        builtin_vars = self.users[user_id]['builtin_vars']
        if resp['content'] is not None:
            builtin_vars["cnt_no_answer_succession"] = 0
            resp['src'] = 'flow'
        if resp['content'] is None:
            qa_kb_response, _ = self.nlu_manager.qa_kb(user_utter)
            if qa_kb_response is not None:
                resp['content'] = qa_kb_response
                resp['src'] = 'kb'
                builtin_vars["cnt_no_answer_succession"] = 0
        if resp['content'] is None:
            qa_kg_answer = self.nlu_manager.qa_kg(user_utter)
            if qa_kg_answer is not None:
                resp['content'] = qa_kg_answer
                resp['src'] = 'kg'
                builtin_vars["cnt_no_answer_succession"] = 0
        if resp['content'] is None:
            builtin_vars["cnt_no_answer_succession"] += 1
            if self.bot_config["fwd"]["switch"] and builtin_vars["cnt_no_answer_succession"] >= self.bot_config["fwd"]["patient"]:
                builtin_vars["cnt_no_answer_succession"] = 0
                resp['content'] = self.service_language['fwd']
                call_status = self.users[user_id]['call_status'] = 'fwd'
            else:
                # 兜底话术
                resp['content'] = response_process(self.service_language['pardon'], g_vars, builtin_vars)
            resp['src'] = 'no_answer'
        return resp, call_status

    def get_response_flow(self, user_id, user_utter):
        """生成除了兜底话术之外的机器人正常回复"""
        user = self.users[user_id]
        resp = {'content': None, 'allow_interrupt': self.interruptable, 'input_channel': self.input_channel_code_map["asr"], 'src': ''}
        g_vars = self.users[user_id]['g_vars']
        builtin_vars = self.users[user_id]['builtin_vars']
        node_stack = self.users[user_id]['node_stack']
        main_flow_node = self.users[user_id]['main_flow_node']

        intent_recognition_done = False
        _, _, current_node = self.get_current_flow_and_node(node_stack, main_flow_node)
        if not current_node or current_node['type'] not in ['slot_filling', 'flow']:
            # 意图识别
            intent = self.intent_recognition(user_utter)
            builtin_vars['intent'] = intent
            intent_recognition_done = True
            # 根据意图识别结果调整node_stack
            if intent is not None:
                if intent not in self.intent_flow_mapping:
                    logging.warning("There is no flow that can be triggered by intent '%s'" % intent)
                else:
                    if not node_stack or self.intent_flow_mapping[intent] != node_stack[0]['flow_name']:
                        # 清空node_stack，把识别到的意图的对应流程压入node_stack
                        if self.flows[self.intent_flow_mapping[intent]].get("forget", True):
                            node_stack.clear()
                        node_stack.append({'flow_name': self.intent_flow_mapping[intent], 'node_id': '0'})
                        # 清空main_flow_node的除'node_id'外的其他信息
                        if main_flow_node:
                            main_flow_node_id = main_flow_node['node_id']
                            main_flow_node.clear()
                            main_flow_node['node_id'] = main_flow_node_id

        # 执行流程，直到得到response
        while not resp['content']:
            # get current node
            # logging.info(g_vars, node_stack)
            current_flow_name, current_flow, current_node = self.get_current_flow_and_node(node_stack, main_flow_node,
                                                                                           verbose=True)
            if current_flow_name is None:
                if intent_recognition_done:
                    break
                else:
                    # 意图识别
                    intent = self.intent_recognition(user_utter)
                    builtin_vars['intent'] = intent
                    intent_recognition_done = True
                    if intent is None:
                        break
                    elif intent not in self.intent_flow_mapping:
                        logging.warning("There is no flow that can be triggered by intent '%s'" % intent)
                        break
                    else:
                        # 清空node_stack，把识别到的意图的对应流程压入node_stack
                        if self.flows[self.intent_flow_mapping[intent]].get("forget", True):
                            node_stack.clear()
                        node_stack.append({'flow_name': self.intent_flow_mapping[intent], 'node_id': '0'})
                        continue

            # log results
            # todo: 每经过一个节点就把该节点的结果追加到results后，有没有更合理的记录对话结果的方法
            user['results'].extend(current_node.get('results', []))

            # process current node
            # branch
            if current_node['type'] == 'branch':
                pass

            # assignment
            elif current_node['type'] == 'assignment':
                for item in current_node['assignments']:
                    g_vars[item['g_vars']] = item['value']

            # response
            elif current_node['type'] == 'response':
                resp_content = ''
                if type(current_node['response']) == str:
                    resp_content = current_node['response']
                elif type(current_node['response']) == dict:
                    resp_content = current_node['response']["content"]
                    resp['input_channel'] = self.input_channel_code_map[current_node['response'].get("input_channel", "asr")]
                resp['content'] = response_process(resp_content, g_vars, builtin_vars)

            # flow
            elif current_node['type'] == 'flow':
                node_info = node_stack[-1] if node_stack else main_flow_node
                if 'return' not in node_info:
                    node_info['return'] = False
                    node_stack.append({'flow_name': current_node['flowName'], 'node_id': '0'})
                    continue
                else:
                    del node_info['return']

            # slot_filling
            elif current_node['type'] == 'slot_filling':
                node_info = node_stack[-1] if node_stack else main_flow_node
                logging.info("enter slot")
                if 'slots_status' not in node_info:
                    node_info['slots_status'] = self.nlu_manager.slots_status_init(current_node['slots'])
                slot_request, slots_filling_finish = self.nlu_manager.slots_filling(node_info['slots_status'],
                                                                                    user_utter,
                                                                                    g_vars)
                if slot_request is not None:
                    resp_content = ''
                    if type(slot_request) == str:
                        resp_content = slot_request
                    elif type(slot_request) == dict:
                        resp_content = slot_request["content"]
                        resp['input_channel'] = self.input_channel_code_map[slot_request.get("input_channel", "asr")]
                    resp['content'] = response_process(resp_content, g_vars, builtin_vars)
                    continue
                if not slots_filling_finish:
                    continue
                else:
                    slots_filling_success = any(
                        slot['value'] is not None for slot in node_info['slots_status']['slots'])
                    del node_info['slots_status']
                    if not slots_filling_success:
                        # 意图识别
                        intent = self.intent_recognition(user_utter)
                        builtin_vars['intent'] = intent
                        intent_recognition_done = True
                        if intent is not None:
                            if intent in self.intent_flow_mapping:
                                # 清空node_stack，把识别到的意图的对应流程压入node_stack
                                if self.flows[self.intent_flow_mapping[intent]].get("forget", True):
                                    node_stack.clear()
                                node_stack.append({'flow_name': self.intent_flow_mapping[intent], 'node_id': '0'})
                                continue
                            else:
                                logging.warning("There is no flow that can be triggered by intent '%s'" % intent)


            # function
            elif current_node['type'] == 'function':
                exec(
                    'builtin_vars["func_return"] = ' + 'functions.' + current_node['funcName'] + '(user_utter, g_vars, context=user)')

            # dm
            assert 'dm' in current_node
            for case in current_node['dm']:
                cond = case['cond']
                cond_is_true = True if cond is True else cond_judge(cond,
                                                                    data={"global": g_vars, "builtin": builtin_vars})
                if cond_is_true or cond == 'else':
                    # 处理nextNode。分当前流程是主流程和非主流程两种情况处理
                    # 非主流程
                    if node_stack:
                        node_stack[-1]['node_id'] = case['nextNode']
                        next_node = current_flow['nodes'][case['nextNode']]
                        if next_node['type'] == 'return':
                            logging.info('flow_name: %s, node_id: %s, node_type: %s' % (
                                current_flow_name, case['nextNode'], next_node['type']))
                            node_stack.pop()
                        elif next_node['type'] == 'exit':
                            logging.info('flow_name: %s, node_id: %s, node_type: %s' % (
                                current_flow_name, case['nextNode'], next_node['type']))
                            if next_node['todo'] == 'hangup':
                                user['call_status'] = 'hangup'
                            elif next_node['todo'] == 'fwd':
                                user['call_status'] = 'fwd'
                            node_stack.clear()
                    # 主流程
                    else:
                        main_flow_node['node_id'] = case['nextNode']
                        next_node = current_flow['nodes'][case['nextNode']]
                        if next_node['type'] == 'return':
                            logging.info('flow_name: %s, node_id: %s, node_type: %s' % (
                                current_flow_name, case['nextNode'], next_node['type']))
                            main_flow_node.clear()
                        elif next_node['type'] == 'exit':
                            logging.info('flow_name: %s, node_id: %s, node_type: %s' % (
                                current_flow_name, case['nextNode'], next_node['type']))
                            if next_node['todo'] == 'hangup':
                                user['call_status'] = 'hangup'
                            elif next_node['todo'] == 'fwd':
                                user['call_status'] = 'fwd'
                            main_flow_node.clear()

                    # 处理response
                    if 'response' in case:
                        resp_content = ''
                        if type(case['response']) == str:
                            resp_content = case['response']
                        elif type(case['response']) == dict:
                            resp_content = case['response']["content"]
                            resp['input_channel'] = self.input_channel_code_map[case['response'].get("input_channel", "asr")]
                        resp['content'] = response_process(resp_content, g_vars, builtin_vars)
                    break
        builtin_vars['last_response'] = resp['content']
        return resp, user['call_status']

    def get_current_flow_and_node(self, node_stack, main_flow_node, verbose=False):
        current_flow_name, current_flow, current_node = None, None, None
        if node_stack:
            current_flow_name = node_stack[-1]['flow_name']
            current_flow = self.flows[current_flow_name]
            curren_node_id = node_stack[-1]['node_id']
            current_node = current_flow['nodes'][curren_node_id]
            if verbose:
                logging.info('flow_name: %s, node_id: %s, node_type: %s' % (
                    current_flow_name, curren_node_id, current_node['type']))
        elif main_flow_node:
            current_flow_name = 'main'
            current_flow = self.flows[current_flow_name]
            curren_node_id = main_flow_node['node_id']
            current_node = current_flow['nodes'][curren_node_id]
            if verbose:
                logging.info('flow_name: %s, node_id: %s, node_type: %s' % (
                    current_flow_name, curren_node_id, current_node['type']))
        return current_flow_name, current_flow, current_node

    def convert_results_to_codes(self, user):
        if self.results_tracker:
            user['results'] = self.results_tracker.convert_results_to_codes(user['results'])
        return user['results']

    def intent_recognition(self, user_utter):
        return self.nlu_manager.intent_recognition(user_utter) if user_utter is not None else None
