# coding=utf-8
import re

def response_process(string, global_vars=None):
	# 把[%global.var_name%]换成对应的变量值
	pattern = '\[%global.\w+%]'
	vars = set(re.findall(pattern, string))
	if global_vars:
		for var in vars:
			var_name = var.split('.')[1].rstrip('%]')
			string = string.replace(var, str(global_vars[var_name]))
	return string


