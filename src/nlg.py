# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Natural language generation based on templates."""

# coding=utf-8
import re

def response_process(string, global_vars=None, builtin_vars=None):
	# 把[%global.var_name%]换成对应的变量值
	pattern = '\[%global.\w+%]'
	vars = set(re.findall(pattern, string))
	if global_vars:
		for var in vars:
			var_name = var.split('.')[1].rstrip('%]')
			if var_name in global_vars:
				string = string.replace(var, str(global_vars[var_name]))
	# 把[%builtin.var_name%]换成对应的变量值
	pattern = '\[%builtin.\w+%]'
	vars = set(re.findall(pattern, string))
	if builtin_vars:
		for var in vars:
			var_name = var.split('.')[1].rstrip('%]')
			if var_name in builtin_vars:
				string = string.replace(var, str(builtin_vars[var_name]))
	return string


