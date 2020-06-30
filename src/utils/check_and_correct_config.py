import glob
import os
import json


def put_else_at_the_end_of_dm(dm):
	else_case = None
	for index, case in enumerate(dm):
		if case['cond'] == 'else':
			else_case = dm.pop(index)
			break
	if else_case:
		dm.append(else_case)
	return dm


if __name__ == '__main__':
	dirname = os.path.dirname(__file__)
	flows_dir = os.path.join(dirname, 'flows')
	flows = {}
	for file in glob.glob(os.path.join(flows_dir, '*.json')):
		with open(file, 'r', encoding='utf-8') as f:
			flows[file] = json.load(f)
	for file in flows:
		for node_id, node in flows[file]['nodes'].items():
			# put_else_at_the_end_of_dm
			if 'dm' in node:
				put_else_at_the_end_of_dm(node['dm'])
			# do something to update config file
			pass
		with open(file, 'w', encoding='utf-8') as f:
			json.dump(flows[file], f, ensure_ascii=False, indent=True)