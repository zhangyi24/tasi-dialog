import logging
from types import SimpleNamespace
from .callwatcher.client import CallManager
from pypinyin import lazy_pinyin
ENV="dev"

if ENV == "production":
    from .api.soap_api import query
else:
    from .api.json_api import query
    
## order_time
def query_phone_by_car_no(user_utter, global_vars, context = None):
    ENDPOINT="users"
    logging.info(f"query_phone_by_car_no: user_utter={user_utter}, context={context}")
    try: 
        if lazy_pinyin(car_no[0])[0][0:3] != "jin":
            return False
    except:
        pass
    data = query(ENDPOINT, car_no=global_vars['car_no'])
    if not data:
        return False
    else:
        global_vars['phone_no'] = data['phone']
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
    global_vars = {'car_no': car_no}
    p_res = query_phone_by_car_no({},global_vars)
    print("query result:", p_res)
    # print(p_res, global_vars)
    car_no_list = ["津A12345", "金123455","晋123456","京123456","冀123456","东","南"]
    for car_no in car_no_list:
        test_tianjin_chepai(car_no)