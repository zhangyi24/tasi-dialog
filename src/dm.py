# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Dialog manage."""

from json_logic import jsonLogic


def cond_judge(cond, data):
	return jsonLogic(cond, data=data)
