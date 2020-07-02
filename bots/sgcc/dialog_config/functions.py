# 自定义函数
def consumer_info_access_by_meter_number(user_utter, global_vars):
	import json
	with open('database/consumers_info.json', 'r', encoding='utf-8') as f:
		consumers_info = json.load(f)
		for consumer_number, consumer_info in consumers_info.items():
			if global_vars['meter_number'] == consumer_info['meter_number']:
				global_vars['consumer_number'] = consumer_number
				global_vars['consumer_info_access'] = True


def verify_consumer_name(user_utter, global_vars):
	import json
	with open('database/consumers_info.json', 'r', encoding='utf-8') as f:
		consumers_info = json.load(f)
		if global_vars['consumer_number'] not in consumers_info:
			global_vars['consumer_verify_success'] = False
			return
		info = consumers_info[global_vars['consumer_number']]
	if info['consName'] in user_utter:
		global_vars['consumer_verify_success'] = True
		global_vars['consumer_name'] = info['consName']
		global_vars['consumer_info'] = info
	else:
		global_vars['consumer_verify_success'] = False


def check_if_reserved_phone_number_exist(user_utter, global_vars):
	import re
	pattern = "^[1][3-9][0-9]{9}$"
	return bool(re.match(pattern, global_vars['consumer_info']['contactMobile']))


def verify_cellphone_number(user_utter, global_vars):
	return global_vars['cellphone_number'] == global_vars['consumer_info']['contactMobile']


def electricity_bill_inquiry(user_utter, global_vars):
	response = '截止到%s年%s月%s日，您的用电量是%s度，电费是%.2f元' % (
		global_vars['consumer_info']['rcvblInfoLists'][0]['releaseDate'][: 4],
		global_vars['consumer_info']['rcvblInfoLists'][0]['releaseDate'][4: 6].lstrip('0'),
		global_vars['consumer_info']['rcvblInfoLists'][0]['releaseDate'][6:].lstrip('0'),
		global_vars['consumer_info']['rcvblInfoLists'][0]['totalPq'],
		global_vars['consumer_info']['rcvblInfoLists'][0]['rcvblAmt'])
	return response


def elec_price_inquiry(user_utter, global_vars):
	elec_price_table = {
		'居民生活用电': {
			'一户一表': [((0, 220), [(1, 0.4900), (float('inf'), 0.4800)]),
			         ((221, 400), [(1, 0.5400), (float('inf'), 0.5300)]),
			         ((400,), [(1, 0.7900), (float('inf'), 0.7800)])],
			'合表': [(1, 0.5100), (float('inf'), 0.5000)]
		},
		'农业生产用电': [(1, 0.5860), (10, 0.5710), (float('inf'), 0.5560)],
		'大工业用电': [(1, 0.6985), (10, 0.6785), (110, 0.6585), (220, 0.6485), (float('inf'), 0.6435)],
		'一般工商业用电': [(1, 0.7932), (10, 0.7750), (110, 0.7206), (220, 0.6913), (float('inf'), 0.6856)],
		'其他': [(1, 0.7932), (10, 0.7750), (110, 0.7206), (220, 0.6913), (float('inf'), 0.6856)]
	}
	
	def pricing(key, price_list):
		for item in price_list:
			if key < item[0]:
				price = item[1]
				return price
	
	def get_volt_kV(volt_string):
		if volt_string[-2:] == 'kV':
			volt_kV = float(volt_string[: -2])
		elif volt_string[-1:] == 'V':
			volt_kV = float(volt_string[: -1]) / 1000
		else:
			print('Invalid voltCode: %s.' % volt_string)
		return volt_kV
	
	response = '经查询，'
	if global_vars['consumer_info']['elecType'] == '居民生活用电':
		if '一户一表' in global_vars['consumer_info']['ruralConsCode']:
			response += '居民一户一表实行阶梯电价。'
			hz = '一二三四五六七八九'
			for i, item in enumerate(elec_price_table['居民生活用电']['一户一表']):
				response += '第%s档每户每月' % hz[i]
				if len(item[0]) == 1:
					response += '%d度以上，' % item[0]
				elif len(item[0]) == 2:
					response += '%d-%d度，' % item[0]
				response += '电价为%.4f元/度。' % pricing(get_volt_kV(global_vars['consumer_info']['voltCode']), item[1])
		elif '合表' in global_vars['consumer_info']['ruralConsCode']:
			price = pricing(get_volt_kV(global_vars['consumer_info']['voltCode']),
			                elec_price_table['居民生活用电']['合表'])
			response += '您执行的电价为%.4f元/度。' % price
	elif global_vars['consumer_info']['elecType'] in elec_price_table:
		price = pricing(get_volt_kV(global_vars['consumer_info']['voltCode']),
		                elec_price_table[global_vars['consumer_info']['elecType']])
		response += '您执行的电价为%.4f元/度。' % price
	else:
		price = pricing(get_volt_kV(global_vars['consumer_info']['voltCode']),
		                elec_price_table['其他'])
		response += '您执行的电价为%.4f元/度。' % price
	return response


def repeat_payment_reponse(user_utter, global_vars):
	response = '经查询，'
	pay_list = global_vars['consumer_info']['payFlowLists']
	if not len(pay_list):
		response += '您本月没有缴费记录。'
	else:
		response += '您本月的有%d条缴费记录。分别在' % len(pay_list)
		for pay in pay_list:
			response += pay['chargeDate']
			if pay['chargeEmpName'][:3] == 'zfb':
				response += '通过支付宝'
			else:
				response += '通过现金'
			response += '缴纳了%s元；' % pay['rcvblAmt']
		response.rstrip('；')
	response += '。如果您有其他缴费行为，建议您向第三方支付平台咨询。'
	return response


def electricity_bill_not_received_response(user_utter, global_vars):
	import datetime
	owe_flag = False
	for owe_info in global_vars['consumer_info']['oweAmtLists']:
		if '欠费' in owe_info['settleFlag']:
			owe_flag = True
			break
	if owe_flag:
		for rcvblInfo in global_vars['consumer_info']['rcvblInfoLists']:
			if '欠费' in rcvblInfo['settleFlag']:
				release_date = map(int, (
				rcvblInfo['releaseDate'][: 4], rcvblInfo['releaseDate'][4: 6], rcvblInfo['releaseDate'][6:]))
				release_date = datetime.date(*release_date)
				penalty_bgn_date = map(int, (
				rcvblInfo['penaltyBgnDate'][: 4], rcvblInfo['penaltyBgnDate'][4: 6], rcvblInfo['penaltyBgnDate'][6:]))
				penalty_bgn_date = datetime.date(*penalty_bgn_date)
				today = datetime.date.today()
				if today > penalty_bgn_date:
					return '经查询，您的电费已过缴费期限，账单无法补寄，您可通过其他途径缴纳电费。'
				elif (today - release_date).days < 4:
					return '经查询，您的电费账单在您电费发行后的3—4天内由抄表员送到您的信箱内，请您耐心等候。'
				else:
					return '我们会尽快为您补寄账单，请您耐心等候。'
	else:
		return '您的电费已结清，无需补寄账单。'


def amount_differ_reponse(user_utter, global_vars):
	import datetime
	today = datetime.datetime.today()
	pay_list = global_vars['consumer_info']['payFlowLists']
	if not len(pay_list):
		response = '未查询到您的缴费信息，建议您向缴费点或第三方支付平台核实。'
		return response
	if len(pay_list) == 1:
		response = '首次购电时会扣除电表费用，经查询您是首次购电，因此实际到账金额少于购电金额。'
		return response
	if len(global_vars['consumer_info']['penaltyInfoLists']):
		penalty = global_vars['consumer_info']['penaltyInfoLists'][0]
		penalty_date = datetime.datetime(int(penalty['rcvedDate'][: 4]), int(penalty['rcvedDate'][4: 6]), int(penalty['rcvedDate'][6:]))
		if penalty['rcvedPenalty'] and (today - penalty_date).days < 30:
			response = '经查询您本月支付了%s月的违约金，因此实际到账金额少于购电金额。' % penalty['rcvblYm']
			return response
	pay = pay_list[0]
	response = '经查询您最近一次的缴费记录为：于%s，缴费%s元，如有异议建议您到当时的缴费点进行核对下缴费金额。' % \
	           (pay['chargeDate'], pay['rcvblAmt'])
	return response


def meter_reading_inquiry(user_utter, global_vars):
	import datetime
	today = datetime.datetime.today()
	if not global_vars['consumer_info']['readPqLists']:
		response = '未查询到您的抄表信息。'
	elif global_vars['meter_reading_month'] == 'CANT_INFORM':
		read = global_vars['consumer_info']['readPqLists'][0]
		response = '您的抄表周期为%s，%s月份的抄表时间是%s，示数为%.4f。' % \
		           (global_vars['consumer_info']['meter_read_cycle'], read['amtYm'][-2:], read['actualYmd'], read['thisRead'])
	else:
		for read in global_vars['consumer_info']['readPqLists']:
			if global_vars['meter_reading_month'] == read['amtYm']:
				response = '您的抄表周期为%s，%s月份的抄表时间是%s，示数为%.4f。' % \
				           (global_vars['consumer_info']['meter_read_cycle'], read['amtYm'][-2:], read['actualYmd'],
				            read['thisRead'])
				return response
		today_ym = str(today.year) + str(today.month)
		if global_vars['meter_reading_month'] < today_ym:
			response = '未查询到%s月份的抄表信息' % global_vars['meter_reading_month'][-2:]
		else:
			read = global_vars['consumer_info']['readPqLists'][0]
			response = '您%s月份暂未抄表，根据你以往的抄表信息，抄表日期预计为%s，建议您稍后再查询。' % \
			           (global_vars['meter_reading_month'][-2:], global_vars['meter_reading_month'] + read['actualYmd'][-2:])
	return response


def get_available_balance(user_utter, global_vars):
	global_vars['available_balance'] = global_vars['consumer_info']['availableBalance']

if __name__ == '__main__':
	global_vars = {'consumers_number': '1234567890'}
