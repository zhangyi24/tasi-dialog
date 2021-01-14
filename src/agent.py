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
from nlg import render_response

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

        self.calls = {}

    def init(self, call_id, user_info, call_info, task_id=-1):
        self.calls[call_id] = {
            "call_id": call_id,
            "g_vars": copy.deepcopy(self.g_vars),
            "builtin_vars": copy.deepcopy(self.builtin_vars),
            "node_stack": [],
            "call_info": call_info,
            "call_status": 'on',
            "history": [],
            "results": self.results_tracker.init_results if self.results_tracker else [],
            "task_id": task_id
        }
        if 'main' in self.flows:
            self.calls[call_id]['node_stack'] = [{"flow_name": "main", "node_id": "0"}]
        # use user_info to init some global variables
        if len(self.g_vars_need_init) != len(user_info):
            logging.warning("The length of 'g_vars_need_init' must be equal to the length of 'user_info': %s != %s",
                            len(self.g_vars_need_init), len(user_info))
        self.calls[call_id]['g_vars'].update(dict(zip(self.g_vars_need_init, user_info)))

    def greeting(self, call_id):
        call = self.calls[call_id]
        # generate response
        resp = self.makeup_bot_response()
        # return first response in main flow as the bot's response
        if 'main' in self.flows:
            resp, call['call_status'] = self.generate_response(call_id, user_utter=None)
            resp['src'] = 'flow'
        # return greeting as the bot's response
        if not resp['content']:
            resp['content'] = render_response(self.service_language['greeting'], self.calls[call_id]['g_vars'],
                                              self.calls[call_id]['builtin_vars'])
            resp['src'] = 'greeting'
        self.calls[call_id]['builtin_vars']['last_response'] = resp['content']
        return resp, call['call_status']

    def response(self, call_id, user_utter):
        """生成机器人回复"""
        resp, call_status = self.generate_response(call_id, user_utter)
        g_vars = self.calls[call_id]['g_vars']
        builtin_vars = self.calls[call_id]['builtin_vars']
        if resp['content'] is not None:
            builtin_vars["cnt_no_answer_succession"] = 0
        if resp['content'] is None:
            qa_kg_answer = self.nlu_manager.qa_kg(user_utter)
            if qa_kg_answer is not None:
                resp['content'] = qa_kg_answer
                resp['src'] = 'kg'
                builtin_vars["cnt_no_answer_succession"] = 0
        if resp['content'] is None:
            builtin_vars["cnt_no_answer_succession"] += 1
            if self.bot_config["fwd"]["switch"] and builtin_vars["cnt_no_answer_succession"] >= self.bot_config["fwd"][
                "patient"]:
                builtin_vars["cnt_no_answer_succession"] = 0
                resp['content'] = self.service_language['fwd']
                call_status = self.calls[call_id]['call_status'] = 'fwd'
            else:
                # 兜底话术
                resp['content'] = render_response(self.service_language['pardon'], g_vars, builtin_vars)
            resp['src'] = 'no_answer'
        self.calls[call_id]['builtin_vars']['last_response'] = resp['content']
        return resp, call_status

    def generate_response(self, call_id, user_utter):
        """生成除了兜底话术之外的机器人正常回复"""
        call = self.calls[call_id]
        resp = self.makeup_bot_response()
        g_vars = self.calls[call_id]['g_vars']
        builtin_vars = self.calls[call_id]['builtin_vars']
        node_stack = self.calls[call_id]['node_stack']

        qa_kb_result = self.nlu_manager.qa_kb(user_utter)
        intent_recognition_result = self.intent_recognition(user_utter)

        intent_recognition_done = False
        _, _, current_node = self.get_current_flow_and_node(node_stack)
        locked_in_flow = self.check_if_locked_in_flow(node_stack)
        intent_is_invasive = intent_recognition_result in self.intent_flow_mapping and self.flows[
            self.intent_flow_mapping[intent_recognition_result]].get("invasive", False)

        # 如果意图对应的流程是侵入性的，直接切换流程
        if intent_is_invasive:
            intent = builtin_vars['intent'] = intent_recognition_result
            intent_recognition_done = True
            # 根据意图识别结果调整node_stack
            if self.update_node_stack(intent, node_stack):
                node_stack[-1]["invade"] = True
        elif (not locked_in_flow) and (not current_node or current_node['type'] not in ['slot_filling', 'flow']):
            if qa_kb_result and qa_kb_result["score"] >= qa_kb_result["threshold"]:
                resp['content'] = qa_kb_result["response"]
                resp['src'] = 'kb'
            else:
                intent = builtin_vars['intent'] = intent_recognition_result
                intent_recognition_done = True
                # 根据意图识别结果调整node_stack
                self.update_node_stack(intent, node_stack)

        # 执行流程，直到得到response
        if not resp['content']:
            while not resp['content']:
                # get current node
                # logging.info(g_vars, node_stack)
                current_flow_name, current_flow, current_node = self.get_current_flow_and_node(node_stack,
                                                                                               verbose=True)
                if current_node is None:
                    if qa_kb_result and qa_kb_result["score"] >= qa_kb_result["threshold"]:
                        resp['content'] = qa_kb_result["response"]
                        resp['src'] = 'kb'
                        break
                    elif intent_recognition_done:
                        break
                    else:
                        intent = builtin_vars['intent'] = intent_recognition_result
                        intent_recognition_done = True
                        self.update_node_stack(intent, node_stack)
                        continue

                # log results
                # todo: 每经过一个节点就把该节点的结果追加到results后，有没有更合理的记录对话结果的方法
                call['results'].extend(current_node.get('results', []))

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
                    self.flow_response_process(resp, current_node['response'], g_vars, builtin_vars)

                # flow
                elif current_node['type'] == 'flow':
                    node_info = node_stack[-1]
                    if 'returned' not in node_info:
                        node_info['returned'] = False
                        node_stack.append({'flow_name': current_node['flowName'], 'node_id': '0'})
                        continue
                    else:
                        del node_info['returned']

                # slot_filling
                elif current_node['type'] == 'slot_filling':
                    node_info = node_stack[-1]
                    logging.info("enter slot_filling node")
                    if 'slots_status' not in node_info:
                        node_info['slots_status'] = self.nlu_manager.slots_status_init(current_node['slots'])
                    slot_request, slots_filling_finish = self.nlu_manager.slots_filling(node_info['slots_status'],
                                                                                        user_utter,
                                                                                        g_vars)
                    if slot_request is not None:
                        self.flow_response_process(resp, slot_request, g_vars, builtin_vars)
                        continue
                    if not slots_filling_finish:
                        continue
                    else:
                        slots_filling_success = any(
                            slot['value'] is not None for slot in node_info['slots_status']['slots'])
                        del node_info['slots_status']
                        locked_in_flow = self.check_if_locked_in_flow(node_stack)
                        if not locked_in_flow and not slots_filling_success:
                            if qa_kb_result and qa_kb_result["score"] >= qa_kb_result["threshold"]:
                                resp['content'] = qa_kb_result["response"]
                                resp['src'] = 'kb'
                                break
                            # 意图识别
                            intent = builtin_vars['intent'] = intent_recognition_result
                            intent_recognition_done = True
                            if self.update_node_stack(intent, node_stack, in_slot_filling_node=True):
                                continue

                # function
                elif current_node['type'] == 'function':
                    exec(
                        'builtin_vars["func_return"] = ' + 'functions.' + current_node[
                            'funcName'] + '(user_utter, g_vars, context=call)')

                # dm
                assert 'dm' in current_node
                for case in current_node['dm']:
                    cond = case['cond']
                    cond_is_true = True if cond is True else cond_judge(cond,
                                                                        data={"global": g_vars,
                                                                              "builtin": builtin_vars})
                    if cond_is_true or cond == 'else':
                        # 处理nextNode。
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
                                    call['call_status'] = 'hangup'
                                elif next_node['todo'] == 'fwd':
                                    call['call_status'] = 'fwd'
                                elif next_node['todo'] == 'ivr':
                                    call['call_status'] = 'ivr'
                                node_stack.clear()
                        # 处理response
                        if 'response' in case:
                            self.flow_response_process(resp, case["response"], g_vars, builtin_vars)
                        break
            if resp['content']:
                resp['src'] = 'flow'
            elif qa_kb_result and qa_kb_result["score"] >= qa_kb_result["threshold2"]:
                resp['content'] = qa_kb_result["response"]
                resp['src'] = 'kb'
        return resp, call['call_status']

    def get_current_flow_and_node(self, node_stack, verbose=False):
        current_flow_name, current_flow, current_node = None, None, None
        if node_stack:
            current_flow_name = node_stack[-1]['flow_name']
            current_flow = self.flows[current_flow_name]
            curren_node_id = node_stack[-1]['node_id']
            current_node = current_flow['nodes'][curren_node_id]
            if verbose:
                logging.info('flow_name: %s, node_id: %s, node_type: %s' % (
                    current_flow_name, curren_node_id, current_node['type']))
        return current_flow_name, current_flow, current_node

    def check_if_locked_in_flow(self, node_stack):
        idx = 0
        for i in range(len(node_stack) - 1, -1, -1):
            if "invade" in node_stack[i]:
                idx = i
                break
        locked_in_flow = any(self.flows[node['flow_name']].get("lock", False) for node in node_stack[idx:])
        return locked_in_flow

    def update_node_stack(self, intent, node_stack, in_slot_filling_node=False):
        if intent is not None:
            if intent not in self.intent_flow_mapping:
                logging.warning("There is no flow that can be triggered by intent '%s'" % intent)
                updated = False
            else:
                idx = -1
                for i in range(len(node_stack) - 1, -1, -1):
                    if "flow_triggered_by_intent" in node_stack[i]:
                        idx = i
                        break
                flow_current = node_stack[idx]['flow_name'] if idx != -1 else None
                flow_target = self.intent_flow_mapping[intent]
                if flow_target != flow_current or in_slot_filling_node:
                    if self.flows[self.intent_flow_mapping[intent]].get("forget", True):
                        # 清空node_stack中除了栈底main流程节点外的其他节点，把识别到的意图的对应流程压入node_stack
                        main_flow_node = node_stack[0] if node_stack and node_stack[0]["flow_name"] == "main" else None
                        node_stack.clear()
                        if main_flow_node:
                            node_stack.append(
                                {'flow_name': main_flow_node['flow_name'], 'node_id': main_flow_node['node_id']})
                    else:
                        if flow_target == flow_current:
                            for _ in range(len(node_stack) - 1, idx - 1, -1):
                                node_stack.clear()
                    node_stack.append({'flow_name': self.intent_flow_mapping[intent], 'node_id': '0'})
                    updated = True
                    node_stack[-1]["flow_triggered_by_intent"] = True
                else:
                    updated = False
        else:
            updated = False
        return updated

    def flow_response_process(self, bot_resp, resp_config_from_flow, g_vars, builtin_vars):
        resp_content = ''
        if type(resp_config_from_flow) == str:
            resp_content = resp_config_from_flow
        elif type(resp_config_from_flow) == dict:
            resp_content = resp_config_from_flow["content"]
            input_channels = resp_config_from_flow.get("input_channels", {})
            asr_switch = input_channels.get("asr", {}).get("switch", True)
            if type(asr_switch) is not bool:
                logging.error(f"type of response.input_channels.asr.switch must be bool instead of {type(asr_switch)}")
            else:
                bot_resp['input_channels']["asr"]["switch"] = asr_switch
            keyboard_switch = input_channels.get("keyboard", {}).get("switch", False)
            if type(keyboard_switch) is not bool:
                logging.error(
                    f"type of response.input_channels.keyboard.switch must be bool instead of {type(keyboard_switch)}")
            else:
                bot_resp['input_channels']["keyboard"]["switch"] = keyboard_switch
            keyboard_max_length = input_channels.get("keyboard", {}).get("max_length", 12)
            if type(keyboard_max_length) is not int or keyboard_max_length not in range(1, 13):
                logging.error(
                    f"type of response.input_channels.keyboard.max_length must be an integer between 1 and 12 instead of {keyboard_max_length}")
            else:
                bot_resp['input_channels']["keyboard"]["max_length"] = keyboard_max_length
        bot_resp['content'] = render_response(resp_content, g_vars, builtin_vars)

    def makeup_bot_response(self, content=None, asr_switch=True, keyboard_switch=False, keyboard_max_length=12,
                            src=''):
        resp = {'content': content, 'allow_interrupt': self.interruptable,
                'input_channels': {"asr": {"switch": asr_switch},
                                   "keyboard": {"switch": keyboard_switch, "max_length": keyboard_max_length}},
                'src': src}
        return resp

    def convert_results_to_codes(self, call):
        if self.results_tracker:
            call['results'] = self.results_tracker.convert_results_to_codes(call['results'])
        return call['results']

    def intent_recognition(self, user_utter):
        return self.nlu_manager.intent_recognition(user_utter) if user_utter is not None else None
