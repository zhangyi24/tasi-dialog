import logging
from types import SimpleNamespace
from .callwatcher.client import CallManager
from pypinyin import lazy_pinyin
import re
ENV="dev"

from .api.json_api import query
    
## order_time
def write_result(user_utter, global_vars, context = None):
    ns = SimpleNamespace(**context)
    call_id = ns.call_info['call_id']
    extend = ns.call_info['extend']
    stringToInt = extend.split("#")[0]
    from_callid = None
    content = "#".join(ns.history)
    call_result = None
    logging.info(f"write_result: extend={extend},call_result={call_result}")
    insert_callout_result(call_id, from_callid, content, extend, call_result)
    return True
    
def render_tts(user_utter, global_vars, context = None):
    car_no=global_vars['car_no']
    global_vars['car_no'] = render_car_no(car_no)
    return True
    
def query_phone_by_car_no(user_utter, global_vars, context = None):
    ENDPOINT="users"
    try: 
        car_no=global_vars['car_no']
        logging.info(f"query_phone_by_car_no: 首字母{lazy_pinyin(car_no[0])[0][0:3]}")
        if lazy_pinyin(car_no[0])[0][0:3] != "jin":
            logging.info(f"query_phone_by_car_no: 非天津车牌")
            return False
    except:
        pass
    
    if ENV == "dev":
        # data = query(ENDPOINT, car_no=global_vars['car_no'])
        # if not data:
        #     return False
        # else:
        #     global_vars['phone_no'] = data['phone']
        #     return True
        global_vars['phone_no'] = 999991
        logging.info(f"query_phone_by_car_no: dev环境返回999991")
        return True
    else:
        global_vars['phone_no'] = 17622627188
        logging.info(f"query_phone_by_car_no: prod环境返回17622627188")
        return True
        
def call_manager_process(user_utter, global_vars, context = None):
    ns = SimpleNamespace(**context)
    call_id = ns.call_info['call_id']
    extend = ns.call_info['extend']
    # global variables
    phone = global_vars['phone_no']
    car_no = global_vars['car_no']
    car_location = global_vars['car_location']
    car_move_reason = global_vars['car_move_reason']
    logging.info(f"call_manager_process: call_id={call_id}, phone={phone}, car_no={car_no}, car_location={car_location}, car_move_reason={car_move_reason}")
    manager = CallManager(call_id, phone, [call_id, car_no, car_location, car_move_reason])
    msg,code = manager.process()
    # Tricky地用global_vars来返回结果
    global_vars['func_message'] = msg
    return code
    
def render_car_no(car_no):
    res = re.sub(r"(\d)", r"{\1}", car_no)
    res = re.sub("([A-Za-z])", r"<\1>", res)
    logging.info(f"渲染{car_no}为{res}")
    return res
    
def test_tianjin_chepai(car_no):
    try: 
        if lazy_pinyin(car_no[0])[0][0:3] != "jin":
            print(f"{car_no} 非天津车牌")
        else:
            print(f"{car_no} 天津车牌")
    except:
        pass
    

if __name__ == "__main__":
    car_no = "津A12345"
    #res = query(f'users',car_no=car_no)
    #print(res)
    # global_vars = {'car_no': car_no}
    # p_res = query_phone_by_car_no({},global_vars)
    # print("query result:", p_res)
    # print(p_res, global_vars)
    car_no_list = ["津A12345", "金AB3455","晋1234CC","京1234R6","冀123456","东","南"]
    for car_no in car_no_list:
        print(render_car_no(car_no))