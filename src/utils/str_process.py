# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Utils for string processing."""

import time
import re
from itertools import product
from io import StringIO
from html.parser import HTMLParser

from pypinyin import pinyin, lazy_pinyin, Style


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_html_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


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
    matches = re.findall(pattern, template)  # 取出模式为()或[]包括其来的子串
    template_with_placeholders = re.sub(pattern, '%s', template)  # 把子串替换成占位符%s
    options_list = []
    for match in matches:
        if match[0] == '(':
            options_list.append(match[1:-1].split('|'))
        elif match[0] == '[':
            options_list.append(match[1:-1].split('|'))
            options_list[-1].append('')
    for values in product(*options_list):
        res.append(template_with_placeholders % values)  # 用搭配替换占位符，得到一个扩展出来的句子。
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
    start = time.time()
    string = '<HTML>登录支付宝账户，点击生活缴费，点击电费按钮，输入十位客户编号选择我已阅读并同意，点击下一步，核实客户户号、户名、地址、当前余额等，输入充值金额，点击立即缴费，输入支付密码，提示支付成功即可。<br><img src="edoc/1583738724276.gif"></HTML>'
    print(strip_html_tags(string))
    print(time.time() - start)
