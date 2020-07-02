from json_logic import jsonLogic


def cond_judge(cond, data):
	return jsonLogic(cond, data=data)
