# coding=utf-8
import requests
import copy

call_id = '25044006'
local_server_url = 'http://127.0.0.1:59999'
remote_server_url = 'http://101.6.68.40:59999'
url = local_server_url
req_body_8 = {
    'userid': call_id,
    'inaction': 8,
    'inparams': {
        'call_id': call_id,
        'call_sor_id': '15652310112',
        'call_dst_id': '053267774615',
        'start_time': '2020-03-14 22:22:37767',
        'entrance_id': '2',
        'flow': 'root.xml',
        'queue_id': '52',
        'extend': '11000000#杭州市#60',
        'strategy_params': '2306#2429719#441'
    }
}

req_body_tts = {
    'userid': call_id,
    'inaction': 9,
    'inparams': {
        'call_id': call_id,
        'inter_idx': '1',
        'begin_play': '2020-03-14 22:22:37909',
        'end_play': '2020-03-14 22:22:47838',
        'result_time': '2020-03-14 22:22:47838',
        'flow_result_type': '3',
        'input': '',
        'inter_no': '2020-03-14 22:22:37909',
        'org': '',
        'grammar': '',
        'newsess': '',
        'res_node_lst': '',
        'res_parse_mode': '',
        'extended_field': ''
    }
}

req_body_asr = {
    'userid': call_id,
    'inaction': 9,
    'inparams': {
        'call_id': call_id,
        'inter_idx': '1',
        'begin_play': '2020-03-14 22:22:47939',
        'end_play': '2020-03-14 22:22:52044',
        'result_time': '2020-03-14 22:22:52044',
        'flow_result_type': '2',
        'input': 'ws_20200401_152240_896681.wav[怎么缴费。]',
        # 'inter_no': '2020-03-14 22:22:47939',
        'inter_no': 'ws_20200401_152240_896681.wav[怎么缴费。]',
        'org': '',
        'grammar': '',
        'newsess': '',
        'res_node_lst': '',
        'res_parse_mode': '',
        'extended_field': ''
    }
}

req_body_tts_asr = {
    'userid': call_id, 'inaction': 9,
    'inparams': {
        'call_id': call_id, 'inter_idx': '1', 'begin_play': '2020-03-15 15:41:20410',
        'end_play': '2020-03-15 15:41:27730', 'result_time': '2020-03-15 15:41:27730',
        'flow_result_type': '1', 'input': '', 'inter_no': '2020-03-15 15:41:20410',
        'org': '', 'grammar': '', 'newsess': '', 'res_node_lst': '', 'res_parse_mode': '',
        'extended_field': ''
    }
}

req_body_user_hangup = {
	'userid': call_id,
	'inaction': 9,
	'inparams': {
		'call_id': call_id,
		'inter_idx': '交互序号',
		"begin_play": "放音开始时间",
		"end_play": "放音结束时间",
		"result_time": "结果产生时间",
		"flow_result_type": '3',
		'input': 'hangup',
		"inter_no": "识别标识",
		"org": "语义资源包",
		"grammar": "语法文件名",
		"newsess": "清空上下文标志",
		"res_node_lst": "小包资源名称",
		"res_parse_mode": "确定资源的优先级",
		"extended_field": "扩展字段，后继新增字段在此字段中拼接"
	}
}

req_body_11 = {
    "userid": call_id,
    "inaction": 11,
    "inparams": {
        "call_id": call_id,
        "inter_idx": "1",
        "begin_trans": "转移的开始时间",
        "end_trans": "转移的结束时间",
        "trans_result": "是否转移成功"
    }
}

req_body_0 = {
    'userid': call_id,
    'inaction': 0,
    'inparams': {
        'call_id': call_id,
        'call_sor_id': '15652310112',
        'call_dst_id': '053267774615',
        'att_status': '1'
    }
}

def get_req_body_tts_asr(user_utter):
    req_body = copy.deepcopy(req_body_tts_asr)
    req_body['inparams'].update({'input': user_utter})
    return req_body


def post(url, req_body):
    resp = requests.post(url=url, json=req_body)
    print(resp.elapsed, resp.json() if resp.content else {})


if __name__ == '__main__':
    post(url, req_body_8)
    user_utters = [
        "发送短信",
        "发送短信",
        "发送短信",
        "发送短信",
        "额",
        "额",
        "额"
    ]
    for user_utter in user_utters:
        req_body = get_req_body_tts_asr(user_utter)
        post(url, req_body)
    post(url, req_body_user_hangup)

