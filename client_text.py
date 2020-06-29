# coding=utf-8
import datetime

import requests

req_body_init = {
	'userid': '',
	'inaction': 8,
	'inparams': {
		'call_id': '',
		'call_sor_id': '',
		'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3],
		'user_info': {}
	}
}

req_body_tts = {
	'userid': '',
	'inaction': 9,
	'inparams': {
		'call_id': '',
		'inter_idx': '',
		'flow_result_type': '3',
		'input': '',
		'inter_no': '',
	}
}

req_body_tts_asr = {
	'userid': '',
	'inaction': 9,
	'inparams': {
		'call_id': '',
		'inter_idx': '',
		'flow_result_type': '2',
		'input': '',
		'inter_no': ''
	}
}

req_body_user_hangup = {
	'userid': '',
	'inaction': 9,
	'inparams': {
		'call_id': '',
		'inter_idx': '',
		"flow_result_type": '3',
		'input': 'hangup'
	}
}

def get_req_body_init(call_id, call_sor_id, user_info):
	req_body = req_body_init
	req_body.update({'userid': call_id})
	req_body['inparams'].update({
		'call_id': call_id,
		'call_sor_id': call_sor_id,
		'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S%f')[:-3],
		'user_info': user_info
	})
	return req_body

def get_req_body_tts(call_id, inter_idx):
	req_body = req_body_tts
	req_body.update({'userid': call_id})
	req_body['inparams'].update({
		'call_id': call_id,
		'inter_idx': inter_idx
	})
	return req_body

def get_req_body_tts_asr(call_id, inter_idx, input, inter_no=''):
	req_body = req_body_tts_asr
	req_body.update({'userid': call_id})
	req_body['inparams'].update({
		'call_id': call_id,
		'inter_idx': inter_idx,
		'input': input,
		'inter_no': inter_no
	})
	return req_body
	

if __name__ == '__main__':
	local_server_url = 'http://127.0.0.1:59998'
	remote_server_url = 'http://101.6.68.40:59998'
	url = local_server_url
	call_id = '123'
	call_sor_id = '130****1234'
	user_info = 'dummy#杭州#60'
	while True:
		req_body = get_req_body_init(call_id, call_sor_id, user_info)
		resp = requests.post(url=url, json=req_body)
		resp_body = resp.json() if resp.content else {}
		while resp_body['outaction'] != '10':
			assert resp_body['outaction'] == '9'
			assert resp_body['outparams']['model_type'] in ['11', '10']
			print('bot:\t%s' % resp_body['outparams']['prompt_text'])
			if resp_body['outparams']['model_type'] == '11':
				req_body = get_req_body_tts_asr(call_id,
				                     resp_body['outparams']['inter_idx'],
				                     input('user:\t'))
			if resp_body['outparams']['model_type'] == '10':
				req_body = get_req_body_tts(call_id, resp_body['outparams']['inter_idx'])
			resp = requests.post(url=url, json=req_body)
			resp_body = resp.json() if resp.content else {}
		if input('continue? (Y?n)').lower() == 'n':
			break
		
		
		