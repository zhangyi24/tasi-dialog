# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Slot filling."""

# coding=utf-8
import sys
import copy
import re
import datetime
import collections
import logging

from nlg import render_response
from utils.str_process import hanzi_to_pinyin

sys.path.append('..')

MAX_REQUEST_NUM = 2

def slots_status_init(slots):
    slots_status = {
        'slots': [],
        'curr_slot_id': 0  # 待填槽id
    }
    for slot in slots:
        slot = copy.deepcopy(slot)
        # 初始化slot状态
        slot['intent'], slot['name'] = slot['name'].split('.')
        slot['times_requested'] = 0
        slot['value'] = None
        if 'response_before_filling' not in slot:
            slot['response_before_filling'] = True
        # max_request_num
        if 'response' in slot:
            slot['max_request_num'] = slot.get('max_request_num', MAX_REQUEST_NUM)
            if type(slot['max_request_num']) is not int or slot['max_request_num'] < 0:
                slot['max_request_num'] = MAX_REQUEST_NUM
        else:
            slot['max_request_num'] = 0
        slots_status['slots'].append(slot)
    return slots_status


def slots_filling(slots_status, user_utter, intents, value_sets, g_vars):
    # resp是机器人的回复，finish是填槽是否结束的标志
    resp, finish = None, True
    # 取出待填槽的状态
    slot = slots_status['slots'][slots_status['curr_slot_id']]
    # 填槽
    if slot['times_requested'] > 0 or not slot['response_before_filling']:
        slot_filling_once(slot, user_utter, intents, value_sets)
    # 检查并修改填槽状态
    while slots_status['curr_slot_id'] < len(slots_status['slots']):
        # 已填
        if slot['value'] is not None:
            if "global_variable" in slot:
                g_vars[slot['global_variable']] = slot['value']
            slots_status['curr_slot_id'] += 1
        # 未填
        else:
            if slot['times_requested'] < slot['max_request_num']:
                resp = slot['response']
                finish = False
                slot['times_requested'] += 1
                break
            else:
                slot['value'] = None
                if "global_variable" in slot:
                    g_vars[slot['global_variable']] = slot['value']
                slots_status['curr_slot_id'] += 1
    return resp, finish


def slot_filling_once(slot, user_utter, intents, value_sets):
    logging.info(f"slot_filling_once\n,slot={slot}\n,intents={intents}\n,user_utter={user_utter}\n")
    """
    更新slot['value']
    """
    if user_utter is None:
        return
    # 获得value_set
    value_set_full_name = intents[slot['intent']]['slots'][slot['name']]['valueSet']
    value_set_from, value_set_name = value_set_full_name.split('.')
    value_set = value_sets[value_set_from][value_set_name]
    # 填槽（字符串匹配）
    if value_set['type'] == 'dict':
        templates = value_set['templates']
        for template in templates:
            template_info = value_set['templates_info'][template]
            search_obj = template_info['regex'].search(user_utter)
            if search_obj:
                slot['value_raw'] = search_obj.group()
                slot['value'] = template_info['standard_value']
                logging.info(
                    "slot_filling: (slot: %s.%s, standard_value: %s, value_raw: %s, template: %s, template_raw: %s)" % (
                        slot['intent'], slot['name'], slot['value'], slot['value_raw'], template,
                        template_info['template_raw']))
                return
        user_utter_pinyin, map_pinyin_idx_hanzi_idx = hanzi_to_pinyin(user_utter)
        for template in templates:
            template_info = value_set['templates_info'][template]
            search_obj = template_info['regex_pinyin'].search(user_utter_pinyin)
            if search_obj:
                span = search_obj.span()
                slot['value_raw'] = user_utter[map_pinyin_idx_hanzi_idx[span[0]]: map_pinyin_idx_hanzi_idx[span[1] + 1]]
                slot['value'] = template_info['standard_value']
                logging.info(
                    "slot_filling: (slot: %s.%s, standard_value: %s, value_raw: %s, template: %s, template_raw: %s)" % (
                        slot['intent'], slot['name'], slot['value'], slot['value_raw'], template,
                        template_info['template_raw']))
                return
    elif value_set['type'] == 'regex':
        search_obj = value_set['regex'].search(user_utter)
        logging.info(f"value_set={value_set['regex']},user_utter={user_utter},search_obj={search_obj}")
        if search_obj:
            slot['value'] = search_obj.group()
    elif value_set['type'] == 'bool':
        slot_filling_bool(slot, user_utter)
    elif value_set['type'] == 'month':
        slot_filling_month(slot, user_utter)


def slot_filling_bool(slot, user_utter):
    slot['value'] = None
    for i in ['没错', '不错']:
        if i in user_utter:
            slot['value'] = True
            break
    if slot['value'] is None:
        for i in ['不知道', '不清楚', '忘了', '记不清']:
            if i in user_utter:
                slot['value'] = None
                break
    if slot['value'] is None:
        for i in ['不', '没']:
            if i in user_utter:
                slot['value'] = False
                break
    if slot['value'] is None:
        slot['value'] = True


def slot_filling_month(slot, user_utter):
    today = datetime.datetime.today()
    if '上上个月' in user_utter:
        month = today.month - 2
        year = today.year
        if month < 1:
            month += 12
            year -= 1
        slot['value'] = '%04d%02d' % (year, month)
    elif '下下个月' in user_utter:
        month = today.month + 2
        year = today.year
        if month > 12:
            month -= 12
            year += 1
        slot['value'] = '%04d%02d' % (year, month)
    elif '上个月' in user_utter:
        month = today.month - 1
        year = today.year
        if month < 1:
            month += 12
            year -= 1
        slot['value'] = '%04d%02d' % (year, month)
    elif '下个月' in user_utter:
        month = today.month + 1
        year = today.year
        if month > 12:
            month -= 12
            year += 1
        slot['value'] = '%04d%02d' % (year, month)
    elif '这个月' in user_utter or '本月' in user_utter:
        slot['value'] = '%04d%02d' % (today.year, today.month)
    else:
        zh_mapping = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '十一': 11,
                      '十二': 12}
        for month in ['十一', '十二', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
                      '12', '11', '10', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            if month in user_utter:
                if month.isdecimal():
                    slot['value'] = '%04d%02d' % (today.year, int(month))
                else:
                    slot['value'] = '%04d%02d' % (today.year, zh_mapping[month])
                break


if __name__ == '__main__':
    pass
