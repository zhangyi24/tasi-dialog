# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Utils for string processing."""

import re
from itertools import product

from pypinyin import pinyin, lazy_pinyin, Style


def expand_template(template):
    """
    Expand the optional boxes in the template.

    Args:
        template: A template with optional boxes. For example: "帮我呼叫(张三|李四)[的电话|的电话号码|的手机]".

    Returns:
        sentences obtained by expanding the template. For example: "帮我呼叫张三", "帮我呼叫张三的电话",
        "帮我呼叫张三的电话号码", "帮我呼叫张三的手机", "帮我呼叫李四", "帮我呼叫李四的电话", "帮我呼叫李四的电话号码", "帮我呼叫李四的手机".
    """
    res = []
    pattern = r'\(.*?\)|\[.*?\]'
    matches = re.findall(pattern, template)     # 取出模式为()或[]包括其来的子串
    template_with_placeholders = re.sub(pattern, '%s', template)    # 把子串替换成占位符%s
    options_list = []
    for match in matches:
        if match[0] == '(':
            options_list.append(match[1:-1].split('|'))
        elif match[0] == '[':
            options_list.append(match[1:-1].split('|'))
            options_list[-1].append('')
    for values in product(*options_list):
        res.append(template_with_placeholders % values)     # 用搭配替换占位符，得到一个扩展出来的句子。
    return res


def get_matches_total_len(pattern, string):
    return len(''.join(re.findall(pattern, string)))


def get_template_len(template):
    return len(template) - get_matches_total_len(r'\.\{\d+\,\d+\}', template)


def hanzi_to_pinyin(hanzi):
    pinyin_list = []
    map_pinyin_idx_hanzi_idx = {0: 0}
    len_pinyin = 0
    for py in pinyin(hanzi):
        pinyin_list.append(py[0])
        len_pinyin += len(py[0]) + 1
        map_pinyin_idx_hanzi_idx[len_pinyin] = len(pinyin_list)
    return ' '.join(pinyin_list), map_pinyin_idx_hanzi_idx


def pattern_to_pinyin(pattern):
    pinyin_list = []
    for py in pinyin(pattern):
        py = py[0]
        if re.fullmatch(r'.{\d?,\d?}', py):
            py = py.replace('.', r'( *\b[^ ]+?\b *)')
            pinyin_list.append(py)
        else:
            pinyin_list.append(py)
            pinyin_list.append(' ')
    pattern_pinyin = ''.join(pinyin_list)
    pattern_pinyin = pattern_pinyin.rstrip()
    return pattern_pinyin


def replace_space(string):
    string = string.strip()
    string = re.sub(r'\s+', '。', string)
    return string


if __name__ == '__main__':
    string = '嗯嗯 \n 好的  打扰了 再见 '
    print(replace_space(string))